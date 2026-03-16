import logging
import os
import select
import signal
import sys
import threading

from mcp.server.fastmcp import FastMCP

from pydantic import ValidationError

from discord_mcp.discord_client import DiscordClient, DiscordAPIError
from discord_mcp.types import Embed, EmbedField

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("discord-mcp")

mcp = FastMCP("discord")

_client: DiscordClient | None = None


def _get_client() -> DiscordClient:
    global _client
    if _client is None:
        token = os.environ.get("DISCORD_BOT_TOKEN", "")
        if not token:
            raise DiscordAPIError("DISCORD_BOT_TOKEN environment variable is not set")
        _client = DiscordClient(bot_token=token)
    return _client


def _handle_shutdown(signum: int, _frame: object) -> None:
    logger.info("Received signal %s, shutting down", signal.Signals(signum).name)
    raise SystemExit(0)


def _watch_stdin() -> None:
    """Detect when the parent closes the stdin pipe and trigger shutdown.

    Uses poll() to watch for POLLHUP without consuming any bytes, so
    the MCP stdio transport keeps working normally.
    """
    try:
        poller = select.poll()
        poller.register(sys.stdin.fileno(), select.POLLHUP)
        while True:
            for _fd, event in poller.poll(1000):
                if event & (select.POLLHUP | select.POLLERR):
                    logger.info("stdin closed, shutting down")
                    os.kill(os.getpid(), signal.SIGTERM)
                    return
    except (OSError, ValueError):
        logger.info("stdin watch failed, shutting down")
        os.kill(os.getpid(), signal.SIGTERM)


def resolve_guild_id(guild_id: str | None) -> str | None:
    if guild_id:
        return guild_id
    return os.environ.get("DISCORD_DEFAULT_GUILD_ID")


async def handle_list_channels(
    client: DiscordClient, guild_id: str
) -> list[dict]:
    channels = await client.list_channels(guild_id)
    return [
        {"id": ch.id, "name": ch.name, "topic": ch.topic, "category": ch.category_name}
        for ch in channels
    ]


async def handle_send_message(
    client: DiscordClient,
    channel: str,
    guild_id: str | None,
    content: str,
) -> dict:
    channel_id = await client.resolve_channel(channel, guild_id)
    result = await client.send_message(channel_id, content=content, embed=None)
    return {"message_id": result.id, "timestamp": result.timestamp}


async def handle_read_messages(
    client: DiscordClient,
    channel: str,
    guild_id: str | None,
    limit: int,
) -> list[dict]:
    channel_id = await client.resolve_channel(channel, guild_id)
    messages = await client.read_messages(channel_id, limit=limit)
    return [
        {
            "id": m.id,
            "author": m.author.username,
            "author_id": m.author.id,
            "content": m.content,
            "timestamp": m.timestamp,
        }
        for m in messages
    ]


async def handle_send_embed(
    client: DiscordClient,
    channel: str,
    guild_id: str | None,
    title: str,
    description: str | None,
    color: int | None,
    fields: list[EmbedField] | None,
    content: str | None,
) -> dict:
    channel_id = await client.resolve_channel(channel, guild_id)
    embed = Embed(
        title=title,
        description=description,
        color=color,
        fields=fields or [],
    )
    result = await client.send_message(
        channel_id, content=content, embed=embed.model_dump(exclude_none=True)
    )
    return {"message_id": result.id, "timestamp": result.timestamp}


@mcp.tool()
async def discord_list_channels(guild_id: str) -> str:
    """List all text channels in a Discord server.

    Args:
        guild_id: The Discord server/guild ID
    """
    try:
        client = _get_client()
        channels = await handle_list_channels(client, guild_id)
        return str(channels)
    except DiscordAPIError as e:
        return f"Error: {e}"
    except ValidationError as e:
        return f"Error: {e.error_count()} validation error(s) in response data"
    except Exception:
        logger.exception("Unexpected error in discord_list_channels")
        return "Error: an unexpected error occurred"


@mcp.tool()
async def discord_send_message(
    channel: str,
    content: str,
    guild_id: str | None = None,
) -> str:
    """Send a plain text message to a Discord channel.

    Args:
        channel: Channel ID or channel name (e.g. "general" or "123456789")
        content: The message text to send
        guild_id: Server/guild ID. Required when channel is a name. Falls back to DISCORD_DEFAULT_GUILD_ID.
    """
    try:
        client = _get_client()
        resolved_guild = resolve_guild_id(guild_id)
        result = await handle_send_message(client, channel, resolved_guild, content)
        return f"Message sent. ID: {result['message_id']}, Timestamp: {result['timestamp']}"
    except DiscordAPIError as e:
        return f"Error: {e}"
    except ValidationError as e:
        return f"Error: {e.error_count()} validation error(s) in response data"
    except Exception:
        logger.exception("Unexpected error in discord_send_message")
        return "Error: an unexpected error occurred"


@mcp.tool()
async def discord_read_messages(
    channel: str,
    guild_id: str | None = None,
    limit: int = 10,
) -> str:
    """Read recent messages from a Discord channel.

    Args:
        channel: Channel ID or channel name
        guild_id: Server/guild ID. Required when channel is a name. Falls back to DISCORD_DEFAULT_GUILD_ID.
        limit: Number of messages to retrieve (default 10, max 50)
    """
    try:
        client = _get_client()
        resolved_guild = resolve_guild_id(guild_id)
        messages = await handle_read_messages(client, channel, resolved_guild, limit)
        return str(messages)
    except DiscordAPIError as e:
        return f"Error: {e}"
    except ValidationError as e:
        return f"Error: {e.error_count()} validation error(s) in response data"
    except Exception:
        logger.exception("Unexpected error in discord_read_messages")
        return "Error: an unexpected error occurred"


@mcp.tool()
async def discord_send_embed(
    channel: str,
    title: str,
    description: str | None = None,
    color: int | None = None,
    fields: list[EmbedField] | None = None,
    content: str | None = None,
    guild_id: str | None = None,
) -> str:
    """Send a rich embed message to a Discord channel.

    Args:
        channel: Channel ID or channel name
        title: Embed title
        description: Embed body text
        color: Embed color as decimal (e.g. 3447003 for blue)
        fields: List of field objects with name, value, and optional inline boolean
        content: Plain text to send alongside the embed
        guild_id: Server/guild ID. Required when channel is a name. Falls back to DISCORD_DEFAULT_GUILD_ID.
    """
    try:
        client = _get_client()
        resolved_guild = resolve_guild_id(guild_id)
        result = await handle_send_embed(
            client, channel, resolved_guild, title, description, color, fields, content
        )
        return f"Embed sent. ID: {result['message_id']}, Timestamp: {result['timestamp']}"
    except DiscordAPIError as e:
        return f"Error: {e}"
    except ValidationError as e:
        return f"Error: {e.error_count()} validation error(s) in response data"
    except Exception:
        logger.exception("Unexpected error in discord_send_embed")
        return "Error: an unexpected error occurred"


def main():
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    watcher = threading.Thread(target=_watch_stdin, daemon=True)
    watcher.start()

    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    guild = os.environ.get("DISCORD_DEFAULT_GUILD_ID")
    logger.info("Discord MCP server starting")
    logger.info("DISCORD_BOT_TOKEN: %s", "set" if token else "NOT SET")
    logger.info("DISCORD_DEFAULT_GUILD_ID: %s", guild or "not set")
    logger.info("Tools: discord_list_channels, discord_send_message, discord_read_messages, discord_send_embed")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
