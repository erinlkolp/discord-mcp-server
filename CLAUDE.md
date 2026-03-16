# CLAUDE.md

## Project Overview

Discord MCP server — exposes Discord REST API v10 as tools in Claude Code via the Model Context Protocol.

## Tech Stack

- Python 3.12+, mcp[cli], httpx, pydantic
- pytest, pytest-asyncio, respx for testing
- Docker for deployment

## Project Structure

```
src/discord_mcp/
├── types.py           — Pydantic models (Channel, Message, SendResult, Embed)
├── discord_client.py  — Async Discord REST API wrapper (httpx)
└── server.py          — MCP tool definitions and handler functions

tests/
├── conftest.py           — Shared fixtures (sample channels, messages)
├── test_types.py         — Pydantic model tests (7 tests)
├── test_discord_client.py — API client tests with respx mocking (14 tests)
└── test_server.py        — MCP tool handler tests (7 tests)
```

## Commands

```bash
# Install (dev)
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run server locally
discord-mcp

# Docker build and run
docker compose build
docker compose run --rm -i discord-mcp
```

## Environment Variables

- `DISCORD_BOT_TOKEN` (required) — Bot auth token
- `DISCORD_DEFAULT_GUILD_ID` (optional) — Default guild for tool calls

## MCP Tools

- `discord_list_channels` — List text channels in a guild
- `discord_send_message` — Send plain text to a channel
- `discord_read_messages` — Read recent messages from a channel
- `discord_send_embed` — Send a rich embed to a channel

## Conventions

- All Discord API interaction goes through `DiscordClient` — never call httpx directly from server.py
- Tool handlers (`handle_*` functions) are separated from `@mcp.tool()` decorators for testability
- Use `DiscordAPIError` for all error conditions
- Tests mock HTTP with `respx`, never hit real Discord API
- Channel resolution is case-insensitive; numeric strings are treated as IDs
- Guild ID fallback chain: explicit parameter → env var → None
- Guild IDs and channel IDs must be validated as numeric snowflakes (`_validate_snowflake`) before URL interpolation
- Embed payloads must go through Pydantic models (`Embed`/`EmbedField`) — never forward raw dicts to the API
- Error messages must not enumerate server structure (e.g., channel lists)
- Dependencies use compatible-release (`~=`) constraints, not open-ended `>=`
- Docker container runs as non-root `appuser`
