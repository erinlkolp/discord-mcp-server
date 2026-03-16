# CLAUDE.md

## Project Overview

Discord MCP server — exposes Discord REST API v10 as tools in Claude Code via the Model Context Protocol.

## Tech Stack

- Python 3.12+, mcp[cli], httpx, pydantic
- pytest, pytest-asyncio, respx for testing
- Docker for deployment

## Project Structure

- `src/discord_mcp/types.py` — Pydantic models for API responses
- `src/discord_mcp/discord_client.py` — Async Discord REST API wrapper
- `src/discord_mcp/server.py` — MCP tool definitions and handlers

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

## Conventions

- All Discord API interaction goes through `DiscordClient` — never call httpx directly from server.py
- Tool handlers are separated from MCP decorators for testability
- Use `DiscordAPIError` for all error conditions
- Tests mock HTTP with `respx`, never hit real Discord API
