import httpx

from discord_mcp.types import Channel, Message, SendResult

BASE_URL = "https://discord.com/api/v10"


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

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an HTTP request, wrapping network errors as DiscordAPIError."""
        try:
            resp = await self._http.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise DiscordAPIError(f"Network error: {e}") from e
        self._check_response(resp)
        return resp

    def _check_response(self, resp: httpx.Response) -> None:
        if resp.is_success:
            return
        try:
            body = resp.json()
            message = body.get("message", resp.text)
        except Exception:
            message = resp.text

        if resp.status_code == 429:
            retry_after = body.get("retry_after", "unknown") if isinstance(body, dict) else "unknown"
            raise DiscordAPIError(
                f"You are being rate limited. retry_after: {retry_after}",
                status_code=429,
            )
        raise DiscordAPIError(
            f"Discord API error {resp.status_code}: {message}",
            status_code=resp.status_code,
        )

    async def list_all_channels(self, guild_id: str) -> list[Channel]:
        """Fetch all channels (all types) for a guild. Used for category name resolution."""
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
        if channel.isdigit():
            return channel
        if not guild_id:
            raise DiscordAPIError(
                "guild_id is required when using channel names and DISCORD_DEFAULT_GUILD_ID is not set"
            )
        channels = await self.list_channels(guild_id)
        for ch in channels:
            if ch.name.lower() == channel.lower():
                return ch.id
        available = ", ".join(ch.name for ch in channels)
        raise DiscordAPIError(
            f"Channel '{channel}' not found in guild. Available text channels: {available}"
        )

    async def send_message(
        self,
        channel_id: str,
        content: str | None = None,
        embed: dict | None = None,
    ) -> SendResult:
        payload: dict = {}
        if content is not None:
            payload["content"] = content
        if embed is not None:
            payload["embeds"] = [embed]
        resp = await self._request("POST", f"/channels/{channel_id}/messages", json=payload)
        return SendResult(**resp.json())

    async def read_messages(self, channel_id: str, limit: int = 10) -> list[Message]:
        clamped = min(max(limit, 1), 50)
        resp = await self._request(
            "GET", f"/channels/{channel_id}/messages", params={"limit": str(clamped)}
        )
        return [Message(**m) for m in resp.json()]
