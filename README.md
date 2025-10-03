# GoCardless MCP Server

A Model Context Protocol (MCP) server for GoCardless API integration, enabling AI assistants to interact with GoCardless payment data.

## Features

This MCP server provides tools to:

- **Customers**: List, get, and create customers
- **Payments**: List, get, and create payments
- **Mandates**: List and get mandates
- **Subscriptions**: List and get subscriptions (including combined details with customer/mandate)
- **Payouts**: List payouts
- **Xero Integration**: Automatic detection and parsing of Xero contact/invoice/payment IDs from metadata

## Limitations

- **Read-only recommended**: While customer and payment creation are supported, read-only API tokens are recommended for most use cases
- **No update operations**: Existing records cannot be modified
- **No cancellation**: Subscriptions, mandates, and payments cannot be cancelled through this server

## Installation

### Using uvx (Recommended for Claude Code/Cursor)

No installation required - uvx will automatically fetch and run the package:

```bash
uvx --from git+https://github.com/jmceleney/gocardless-mcp.git gocardless-mcp
```

Configure in your MCP settings (see configuration examples below).

### Using pipx

```bash
pipx install git+https://github.com/jmceleney/gocardless-mcp.git
```

### Using pip

```bash
pip install git+https://github.com/jmceleney/gocardless-mcp.git
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/jmceleney/gocardless-mcp.git
cd gocardless-mcp

# Install in development mode
pip install -e .
```

## Configuration

### Environment Variables

You'll need to configure these environment variables:

- `GOCARDLESS_ACCESS_TOKEN` (required): Your GoCardless API access token
- `GOCARDLESS_ENVIRONMENT` (optional): Either `sandbox` or `live` (defaults to `sandbox`)

**Get a GoCardless Access Token:**
1. Sign up for a [GoCardless sandbox account](https://manage-sandbox.gocardless.com/signup)
2. Navigate to Developers > API tokens
3. Create a new access token
4. Copy the token for use in configuration

## Setup for Different AI Tools

### Claude Desktop

Claude Desktop is the easiest way to get started with MCP servers.

**Configuration file location:**
- **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

**Add this configuration:**

```json
{
  "mcpServers": {
    "gocardless": {
      "command": "gocardless-mcp",
      "env": {
        "GOCARDLESS_ACCESS_TOKEN": "your_access_token_here",
        "GOCARDLESS_ENVIRONMENT": "sandbox"
      }
    }
  }
}
```

**After configuration:**
1. Restart Claude Desktop
2. Look for the 🔨 (hammer) icon in the bottom-right corner
3. Click it to verify the GoCardless server is connected
4. Start asking questions like "Show me my recent GoCardless customers"

### Claude Code

Claude Code works best with uvx for automatic package management.

**Method 1: Using uvx (Recommended)**

```bash
claude mcp add gocardless \
  --env GOCARDLESS_ACCESS_TOKEN=your_token_here \
  --env GOCARDLESS_ENVIRONMENT=sandbox \
  -- uvx --from git+https://github.com/jmceleney/gocardless-mcp.git gocardless-mcp
```

**Method 2: Edit Configuration File Directly**

Edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "gocardless": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jmceleney/gocardless-mcp.git", "gocardless-mcp"],
      "env": {
        "GOCARDLESS_ACCESS_TOKEN": "your_access_token_here",
        "GOCARDLESS_ENVIRONMENT": "sandbox"
      }
    }
  }
}
```

**After configuration:**
1. Restart Claude Code
2. Verify with: `claude mcp list`
3. The GoCardless server should appear in the list

### Cursor IDE

Cursor works best with uvx for automatic package management.

**Project-specific configuration** (recommended):

Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "gocardless": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jmceleney/gocardless-mcp.git", "gocardless-mcp"],
      "env": {
        "GOCARDLESS_ACCESS_TOKEN": "your_access_token_here",
        "GOCARDLESS_ENVIRONMENT": "sandbox"
      }
    }
  }
}
```

**Global configuration** (available in all projects):

Create `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gocardless": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jmceleney/gocardless-mcp.git", "gocardless-mcp"],
      "env": {
        "GOCARDLESS_ACCESS_TOKEN": "your_access_token_here",
        "GOCARDLESS_ENVIRONMENT": "sandbox"
      }
    }
  }
}
```

**After configuration:**
1. Restart Cursor
2. Open the MCP settings page to verify the server is connected
3. The Composer Agent will automatically use GoCardless tools when relevant

### Other MCP Clients

For any MCP client that supports stdio transport:

```bash
# Make sure environment variables are set
export GOCARDLESS_ACCESS_TOKEN="your_token_here"
export GOCARDLESS_ENVIRONMENT="sandbox"

# Run the server
gocardless-mcp
```

The server communicates via JSON-RPC over stdin/stdout, so it won't produce output when run directly.

## Data Hierarchy

GoCardless data follows this hierarchy:
- **Customer** (CU*) → **Mandate** (MD*) → **Subscription** (SB*) / **Payment** (PM*)

Mandates authorize recurring payments. Subscriptions generate recurring payments automatically.

## Available Tools

### Customer Tools

- `list_customers`: List all customers (optional limit parameter)
- `get_customer`: Get a specific customer by ID
- `create_customer`: Create a new customer (requires email, optional given_name, family_name, company_name)

### Payment Tools

- `list_payments`: List payments (optional limit, status, subscription, mandate filters)
- `get_payment`: Get a specific payment by ID (includes links to mandate/subscription)
- `create_payment`: Create a new payment (requires amount, currency, mandate_id, optional description)

### Mandate Tools

- `list_mandates`: List mandates (optional limit and customer parameters)
- `get_mandate`: Get a specific mandate by ID (includes link to customer)

### Subscription Tools

- `list_subscriptions`: List subscriptions (optional limit and status parameters)
- `get_subscription`: Get a specific subscription by ID (includes link to mandate)
- `get_subscription_details`: Get complete subscription info including mandate and customer in one call

### Payout Tools

- `list_payouts`: List payouts (optional limit parameter)

## Usage Examples

Once configured in Claude Desktop, you can ask:

- "Show me my recent GoCardless customers"
- "Get details for customer CU123"
- "Create a new customer with email test@example.com"
- "List all pending payments"
- "Show me the details of payment PM123"

## Development & Testing

### Testing with MCP Inspector

The MCP Inspector provides an interactive web interface to test your server:

```bash
# Run the inspector (requires Node.js)
npx @modelcontextprotocol/inspector gocardless-mcp
```

This will:
1. Start the inspector on `http://localhost:6274`
2. Open your browser automatically
3. Allow you to set environment variables in the UI
4. Interactively test all available tools

**In the Inspector:**
1. Set your `GOCARDLESS_ACCESS_TOKEN` in the environment variables section
2. Set `GOCARDLESS_ENVIRONMENT` to `sandbox`
3. Browse available tools on the left sidebar
4. Click any tool to see its schema
5. Fill in parameters and click "Run" to test

### Testing with a Python Client

Create a test script to programmatically test the server:

```python
import asyncio
import os
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def main():
    server_params = StdioServerParameters(
        command="gocardless-mcp",
        env={
            "GOCARDLESS_ACCESS_TOKEN": "your_sandbox_token",
            "GOCARDLESS_ENVIRONMENT": "sandbox"
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Test a tool
            result = await session.call_tool("list_customers", {"limit": 5})
            print("\nResult:", result)

asyncio.run(main())
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (when implemented)
pytest
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
