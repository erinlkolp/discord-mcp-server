# Discord MCP Server

A Python MCP (Model Context Protocol) server that lets you interact with Discord directly from Claude Code sessions. Send messages, read channels, post rich embeds, and list server channels — all through natural conversation with Claude.

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Claude Code** CLI installed
- A **Discord bot token** (setup guide below)

## Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**, give it a name, and create it
3. Go to **Bot** in the left sidebar
4. Click **Reset Token** and copy the token — this is your `DISCORD_BOT_TOKEN`
5. Under **Privileged Gateway Intents**, enable **Message Content Intent**
6. Go to **OAuth2 > URL Generator** in the left sidebar
7. Select scopes: `bot`
8. Select bot permissions: `Send Messages`, `Read Message History`, `View Channels`
9. Copy the generated URL and open it in your browser to invite the bot to your server

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd slack-claude-skill  # Note: directory name is a legacy artifact; this is a Discord MCP server
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your DISCORD_BOT_TOKEN
```

### 3. Build the Docker image

```bash
docker compose build
```

### 4. Register with Claude Code

Add the following to your Claude Code MCP settings. You can configure this in
`~/.claude/settings.json` (global) or `.mcp.json` (project-level):

```json
{
  "mcpServers": {
    "discord": {
      "command": "docker",
      "args": [
        "compose",
        "-f", "/absolute/path/to/slack-claude-skill/docker-compose.yml",
        "run", "--rm", "-i", "discord-mcp"
      ],
      "env": {
        "DISCORD_BOT_TOKEN": "your-bot-token-here",
        "DISCORD_DEFAULT_GUILD_ID": "your-guild-id-here"
      }
    }
  }
}
```

> **Note:** Replace `/absolute/path/to/slack-claude-skill` with the actual
> absolute path to this project on your machine. Replace the token and guild ID
> with your actual values.

## Usage Examples

Once configured, you can use these tools in any Claude Code session:

**List channels in a server:**
> "Show me all the channels in my Discord server"

**Send a message:**
> "Send 'Deployment complete!' to the #general channel"

**Read recent messages:**
> "What are the last 5 messages in #random?"

**Send a rich embed:**
> "Send an embed to #updates with title 'Release v2.0' and a green color, with fields for 'Changes' and 'Breaking Changes'"

## Tool Reference

### discord_list_channels

Lists all text channels in a Discord server.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `guild_id` | string | Yes | Discord server/guild ID |

### discord_send_message

Sends a plain text message to a channel.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | string | Yes | Channel ID or name (e.g. `"general"`) |
| `content` | string | Yes | Message text |
| `guild_id` | string | No | Server ID. Required if channel is a name and no default is set. |

### discord_read_messages

Reads recent messages from a channel.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | string | Yes | Channel ID or name |
| `guild_id` | string | No | Server ID. Required if channel is a name and no default is set. |
| `limit` | integer | No | Number of messages (default: 10, max: 50) |

### discord_send_embed

Sends a rich embed message to a channel.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | string | Yes | Channel ID or name |
| `title` | string | Yes | Embed title |
| `description` | string | No | Embed body text |
| `color` | integer | No | Color as decimal (e.g. `3447003` for blue) |
| `fields` | list | No | List of `{name, value, inline}` objects |
| `content` | string | No | Plain text alongside the embed |
| `guild_id` | string | No | Server ID. Required if channel is a name and no default is set. |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Bot token from Discord Developer Portal |
| `DISCORD_DEFAULT_GUILD_ID` | No | Default server ID for all tool calls |

## Development

### Running locally (without Docker)

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Set environment variables
export DISCORD_BOT_TOKEN=your-token
export DISCORD_DEFAULT_GUILD_ID=your-guild-id

# Run the server
discord-mcp
```

### Running tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
