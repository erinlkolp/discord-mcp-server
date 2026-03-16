import asyncio
import re

import httpx

from discord_mcp.types import Channel, Message, SendResult, MAX_MESSAGE_CONTENT

BASE_URL = "https://discord.com/api/v10"

_SNOWFLAKE_RE = re.compile(r"^\d{1,20}$")


def _validate_snowflake(value: str, name: str) -> None:
    if not _SNOWFLAKE_RE.match(value):
        raise DiscordAPIError(f"Invalid {name}: must be a numeric ID")


class DiscordAPIError(Exception):
    """Raised when a Discord API call fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class DiscordClient:
    def __init__(self, bot_token: str):
        self._http = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bot {bot_token}"},
            timeout=30.0,
        )

    async def close(self):
        await self._http.aclose()

    async def _request(
        self, method: str, path: str, _retries: int = 1, **kwargs
    ) -> httpx.Response:
        """Make an HTTP request, retrying once on rate limit."""
        try:
            resp = await self._http.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise DiscordAPIError("Network error communicating with Discord") from e
        if resp.status_code == 429 and _retries > 0:
            body = {}
            try:
                body = resp.json()
            except Exception:
                pass
            retry_after = float(body.get("retry_after", 1))
            retry_after = min(retry_after, 5.0)
            await asyncio.sleep(retry_after)
            return await self._request(method, path, _retries=_retries - 1, **kwargs)
        self._check_response(resp)
        return resp

    _SAFE_ERROR_MESSAGES: dict[int, str] = {
        400: "Bad request",
        401: "Authentication failed",
        403: "Permission denied",
        404: "Resource not found",
    }

    def _check_response(self, resp: httpx.Response) -> None:
        if resp.is_success:
            return

        if resp.status_code == 429:
            body: dict = {}
            try:
                body = resp.json()
            except Exception:
                pass
            retry_after = body.get("retry_after", "unknown")
            raise DiscordAPIError(
                f"You are being rate limited. retry_after: {retry_after}",
                status_code=429,
            )

        safe_message = self._SAFE_ERROR_MESSAGES.get(
            resp.status_code, f"Discord API error {resp.status_code}"
        )
        raise DiscordAPIError(safe_message, status_code=resp.status_code)

    async def list_all_channels(self, guild_id: str) -> list[Channel]:
        """Fetch all channels (all types) for a guild. Used for category name resolution."""
        _validate_snowflake(guild_id, "guild_id")
        resp = await self._request("GET", f"/guilds/{guild_id}/channels")
        return [Channel(**ch) for ch in resp.json()]

    async def list_channels(self, guild_id: str) -> list[Channel]:
        """Fetch only text channels (type 0) with category names resolved."""
        all_channels = await self.list_all_channels(guild_id)
        # Build category ID -> name map (type 4 = category)
        categories = {ch.id: ch.name for ch in all_channels if ch.type == 4}
        text_channels = [ch for ch in all_channels if ch.type == 0]
        for ch in text_channels:
            ch.category_name = categories.get(ch.parent_id) if ch.parent_id else None
        return text_channels

    async def resolve_channel(self, channel: str, guild_id: str | None) -> str:
        if _SNOWFLAKE_RE.match(channel):
            return channel
        if not guild_id:
            raise DiscordAPIError(
                "guild_id is required when using channel names and DISCORD_DEFAULT_GUILD_ID is not set"
            )
        channels = await self.list_channels(guild_id)
        for ch in channels:
            if ch.name.lower() == channel.lower():
                return ch.id
        raise DiscordAPIError(
            f"Channel '{channel}' not found in guild"
        )

    async def send_message(
        self,
        channel_id: str,
        content: str | None = None,
        embed: dict | None = None,
    ) -> SendResult:
        _validate_snowflake(channel_id, "channel_id")
        if content is not None and len(content) > MAX_MESSAGE_CONTENT:
            raise DiscordAPIError(
                f"Message content exceeds {MAX_MESSAGE_CONTENT} characters"
            )
        payload: dict = {}
        if content is not None:
            payload["content"] = content
        if embed is not None:
            payload["embeds"] = [embed]
        resp = await self._request("POST", f"/channels/{channel_id}/messages", json=payload)
        return SendResult(**resp.json())

    async def read_messages(self, channel_id: str, limit: int = 10) -> list[Message]:
        _validate_snowflake(channel_id, "channel_id")
        clamped = min(max(limit, 1), 50)
        resp = await self._request(
            "GET", f"/channels/{channel_id}/messages", params={"limit": str(clamped)}
        )
        return [Message(**m) for m in resp.json()]
