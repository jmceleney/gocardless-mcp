"""GoCardless MCP Server implementation."""

import asyncio
import os
from typing import Any

import gocardless_pro
import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions


def get_client() -> gocardless_pro.Client:
    """Initialize and return GoCardless client."""
    access_token = os.environ.get("GOCARDLESS_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("GOCARDLESS_ACCESS_TOKEN environment variable is required")

    environment = os.environ.get("GOCARDLESS_ENVIRONMENT", "sandbox")
    return gocardless_pro.Client(access_token=access_token, environment=environment)


server = Server("gocardless-mcp")

# Server instructions for AI agents
SERVER_INSTRUCTIONS = """GoCardless payment data hierarchy: Customer (CU*) → Mandate (MD*) → Subscription (SB*) / Payment (PM*).
Use get_subscription_details for complete subscription info. Follow links in responses to traverse relationships.

Xero integration: metadata.xero field contains JSON string with Xero UUIDs:
- Customers/Mandates: {"contact":"<xero-contact-id>"}
- Payments: {"invoice":"<xero-invoice-id>","payment":"<xero-payment-id>"}"""


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available GoCardless tools."""
    return [
        types.Tool(
            name="list_customers",
            description="List all customers from GoCardless",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of customers to retrieve (default: 50)",
                    }
                },
            },
        ),
        types.Tool(
            name="get_customer",
            description="Get a specific customer by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The GoCardless customer ID (e.g., CU123)",
                    }
                },
                "required": ["customer_id"],
            },
        ),
        types.Tool(
            name="create_customer",
            description="Create a new customer in GoCardless",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Customer email address",
                    },
                    "given_name": {
                        "type": "string",
                        "description": "Customer first name",
                    },
                    "family_name": {
                        "type": "string",
                        "description": "Customer last name",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Customer company name (optional)",
                    },
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="list_payments",
            description="List payments from GoCardless",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of payments to retrieve (default: 50)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by payment status (pending_customer_approval, pending_submission, submitted, confirmed, paid_out, cancelled, customer_approval_denied, failed, charged_back)",
                    },
                    "subscription": {
                        "type": "string",
                        "description": "Filter by subscription ID (e.g., SB123)",
                    },
                    "mandate": {
                        "type": "string",
                        "description": "Filter by mandate ID (e.g., MD123)",
                    },
                },
            },
        ),
        types.Tool(
            name="get_payment",
            description="Get a specific payment by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": "The GoCardless payment ID (e.g., PM123)",
                    }
                },
                "required": ["payment_id"],
            },
        ),
        types.Tool(
            name="create_payment",
            description="Create a new payment in GoCardless",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "integer",
                        "description": "Amount in minor currency unit (e.g., 1000 for £10.00)",
                    },
                    "currency": {
                        "type": "string",
                        "description": "ISO 4217 currency code (e.g., GBP, EUR)",
                    },
                    "mandate_id": {
                        "type": "string",
                        "description": "ID of the mandate to use for this payment",
                    },
                    "description": {
                        "type": "string",
                        "description": "Payment description",
                    },
                },
                "required": ["amount", "currency", "mandate_id"],
            },
        ),
        types.Tool(
            name="list_mandates",
            description="List mandates from GoCardless",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of mandates to retrieve (default: 50)",
                    },
                    "customer": {
                        "type": "string",
                        "description": "Filter by customer ID",
                    },
                },
            },
        ),
        types.Tool(
            name="get_mandate",
            description="Get a specific mandate by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "mandate_id": {
                        "type": "string",
                        "description": "The GoCardless mandate ID (e.g., MD123)",
                    }
                },
                "required": ["mandate_id"],
            },
        ),
        types.Tool(
            name="list_subscriptions",
            description="List subscriptions from GoCardless",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of subscriptions to retrieve (default: 50)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by subscription status",
                    },
                },
            },
        ),
        types.Tool(
            name="get_subscription",
            description="Get subscription by ID. Returns links.mandate - use get_mandate then get_customer for full details, or use get_subscription_details instead.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "description": "The GoCardless subscription ID (e.g., SB123)",
                    }
                },
                "required": ["subscription_id"],
            },
        ),
        types.Tool(
            name="get_subscription_details",
            description="Get complete subscription info including mandate and customer in one call",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "description": "The GoCardless subscription ID (e.g., SB123)",
                    }
                },
                "required": ["subscription_id"],
            },
        ),
        types.Tool(
            name="list_payouts",
            description="List payouts from GoCardless",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of payouts to retrieve (default: 50)",
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool calls for GoCardless operations."""
    client = get_client()

    try:
        if name == "list_customers":
            limit = arguments.get("limit", 50)
            customers = client.customers.list(params={"limit": limit})
            result = []
            for customer in customers.records:
                result.append(
                    {
                        "id": customer.id,
                        "email": customer.email,
                        "given_name": customer.given_name,
                        "family_name": customer.family_name,
                        "company_name": customer.company_name,
                        "created_at": customer.created_at,
                    }
                )
            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(result)} customers:\n{_format_json(result)}",
                )
            ]

        elif name == "get_customer":
            customer_id = arguments["customer_id"]
            customer = client.customers.get(customer_id)
            result = {
                "id": customer.id,
                "email": customer.email,
                "given_name": customer.given_name,
                "family_name": customer.family_name,
                "company_name": customer.company_name,
                "created_at": customer.created_at,
                "address_line1": customer.address_line1,
                "address_line2": customer.address_line2,
                "city": customer.city,
                "postal_code": customer.postal_code,
                "country_code": customer.country_code,
                "metadata": customer.metadata if hasattr(customer, 'metadata') else {},
            }
            return [
                types.TextContent(type="text", text=_format_json(result))
            ]

        elif name == "create_customer":
            params = {
                "email": arguments["email"],
            }
            if "given_name" in arguments:
                params["given_name"] = arguments["given_name"]
            if "family_name" in arguments:
                params["family_name"] = arguments["family_name"]
            if "company_name" in arguments:
                params["company_name"] = arguments["company_name"]

            customer = client.customers.create(params=params)
            return [
                types.TextContent(
                    type="text",
                    text=f"Customer created successfully:\n{_format_json({'id': customer.id, 'email': customer.email})}",
                )
            ]

        elif name == "list_payments":
            params = {"limit": arguments.get("limit", 50)}
            if "status" in arguments:
                params["status"] = arguments["status"]
            if "subscription" in arguments:
                params["subscription"] = arguments["subscription"]
            if "mandate" in arguments:
                params["mandate"] = arguments["mandate"]

            payments = client.payments.list(params=params)
            result = []
            for payment in payments.records:
                result.append(
                    {
                        "id": payment.id,
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "status": payment.status,
                        "description": payment.description,
                        "created_at": payment.created_at,
                    }
                )
            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(result)} payments:\n{_format_json(result)}",
                )
            ]

        elif name == "get_payment":
            payment_id = arguments["payment_id"]
            payment = client.payments.get(payment_id)
            result = {
                "id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "description": payment.description,
                "created_at": payment.created_at,
                "charge_date": payment.charge_date,
                "metadata": payment.metadata if hasattr(payment, 'metadata') else {},
                "links": {
                    "mandate": payment.links.mandate if hasattr(payment, 'links') and hasattr(payment.links, 'mandate') else None,
                    "subscription": payment.links.subscription if hasattr(payment, 'links') and hasattr(payment.links, 'subscription') else None,
                },
            }
            return [
                types.TextContent(type="text", text=_format_json(result))
            ]

        elif name == "create_payment":
            params = {
                "amount": arguments["amount"],
                "currency": arguments["currency"],
                "links": {"mandate": arguments["mandate_id"]},
            }
            if "description" in arguments:
                params["description"] = arguments["description"]

            payment = client.payments.create(params=params)
            return [
                types.TextContent(
                    type="text",
                    text=f"Payment created successfully:\n{_format_json({'id': payment.id, 'amount': payment.amount, 'currency': payment.currency, 'status': payment.status})}",
                )
            ]

        elif name == "list_mandates":
            params = {"limit": arguments.get("limit", 50)}
            if "customer" in arguments:
                params["customer"] = arguments["customer"]

            mandates = client.mandates.list(params=params)
            result = []
            for mandate in mandates.records:
                result.append(
                    {
                        "id": mandate.id,
                        "status": mandate.status,
                        "scheme": mandate.scheme,
                        "created_at": mandate.created_at,
                    }
                )
            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(result)} mandates:\n{_format_json(result)}",
                )
            ]

        elif name == "get_mandate":
            mandate_id = arguments["mandate_id"]
            mandate = client.mandates.get(mandate_id)
            result = {
                "id": mandate.id,
                "status": mandate.status,
                "scheme": mandate.scheme,
                "created_at": mandate.created_at,
                "reference": mandate.reference,
                "metadata": mandate.metadata if hasattr(mandate, 'metadata') else {},
                "links": {
                    "customer": mandate.links.customer if hasattr(mandate, 'links') else None,
                },
            }
            return [
                types.TextContent(type="text", text=_format_json(result))
            ]

        elif name == "list_subscriptions":
            params = {"limit": arguments.get("limit", 50)}
            if "status" in arguments:
                params["status"] = arguments["status"]

            subscriptions = client.subscriptions.list(params=params)
            result = []
            for subscription in subscriptions.records:
                result.append(
                    {
                        "id": subscription.id,
                        "amount": subscription.amount,
                        "currency": subscription.currency,
                        "status": subscription.status,
                        "created_at": subscription.created_at,
                    }
                )
            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(result)} subscriptions:\n{_format_json(result)}",
                )
            ]

        elif name == "get_subscription":
            subscription_id = arguments["subscription_id"]
            subscription = client.subscriptions.get(subscription_id)
            result = {
                "id": subscription.id,
                "amount": subscription.amount,
                "currency": subscription.currency,
                "status": subscription.status,
                "interval_unit": subscription.interval_unit,
                "interval": subscription.interval,
                "created_at": subscription.created_at,
                "name": subscription.name,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "metadata": subscription.metadata if hasattr(subscription, 'metadata') else {},
                "links": {
                    "mandate": subscription.links.mandate if hasattr(subscription, 'links') else None,
                },
            }
            return [
                types.TextContent(type="text", text=_format_json(result))
            ]

        elif name == "get_subscription_details":
            subscription_id = arguments["subscription_id"]

            # Get subscription
            subscription = client.subscriptions.get(subscription_id)

            # Get mandate
            mandate = client.mandates.get(subscription.links.mandate)

            # Get customer
            customer = client.customers.get(mandate.links.customer)

            result = {
                "subscription": {
                    "id": subscription.id,
                    "name": subscription.name,
                    "amount": subscription.amount,
                    "currency": subscription.currency,
                    "status": subscription.status,
                    "interval_unit": subscription.interval_unit,
                    "interval": subscription.interval,
                    "start_date": subscription.start_date,
                    "end_date": subscription.end_date,
                    "created_at": subscription.created_at,
                    "metadata": subscription.metadata if hasattr(subscription, 'metadata') else {},
                },
                "mandate": {
                    "id": mandate.id,
                    "reference": mandate.reference,
                    "status": mandate.status,
                    "scheme": mandate.scheme,
                    "created_at": mandate.created_at,
                    "metadata": mandate.metadata if hasattr(mandate, 'metadata') else {},
                },
                "customer": {
                    "id": customer.id,
                    "email": customer.email,
                    "given_name": customer.given_name,
                    "family_name": customer.family_name,
                    "company_name": customer.company_name,
                    "address_line1": customer.address_line1,
                    "address_line2": customer.address_line2,
                    "city": customer.city,
                    "postal_code": customer.postal_code,
                    "country_code": customer.country_code,
                    "created_at": customer.created_at,
                    "metadata": customer.metadata if hasattr(customer, 'metadata') else {},
                },
            }
            return [
                types.TextContent(type="text", text=_format_json(result))
            ]

        elif name == "list_payouts":
            limit = arguments.get("limit", 50)
            payouts = client.payouts.list(params={"limit": limit})
            result = []
            for payout in payouts.records:
                result.append(
                    {
                        "id": payout.id,
                        "amount": payout.amount,
                        "currency": payout.currency,
                        "status": payout.status,
                        "created_at": payout.created_at,
                    }
                )
            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(result)} payouts:\n{_format_json(result)}",
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [
            types.TextContent(
                type="text", text=f"Error executing {name}: {str(e)}"
            )
        ]


def _format_json(data: Any) -> str:
    """Format data as JSON string."""
    import json
    return json.dumps(data, indent=2)


async def run():
    """Run the GoCardless MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="gocardless-mcp",
            server_version="0.1.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(read_stream, write_stream, init_options)


def main():
    """Entry point for the server script."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
