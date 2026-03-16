import httpx
import pytest
import respx

from discord_mcp.discord_client import DiscordClient, DiscordAPIError

BASE = "https://discord.com/api/v10"


@pytest.fixture
def client():
    return DiscordClient(bot_token="test-token")


class TestListChannels:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_text_channels(self, client, sample_channels):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            return_value=httpx.Response(200, json=sample_channels)
        )
        channels = await client.list_channels("111222333444555666")
        # Should exclude voice (type 2) and category (type 4)
        assert len(channels) == 2
        assert channels[0].name == "general"
        assert channels[1].name == "random"


class TestResolveChannel:
    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_by_name(self, client, sample_channels):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            return_value=httpx.Response(200, json=sample_channels)
        )
        channel_id = await client.resolve_channel("general", "111222333444555666")
        assert channel_id == "100"

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_by_name_case_insensitive(self, client, sample_channels):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            return_value=httpx.Response(200, json=sample_channels)
        )
        channel_id = await client.resolve_channel("General", "111222333444555666")
        assert channel_id == "100"

    @pytest.mark.asyncio
    async def test_resolve_numeric_id_passthrough(self, client):
        channel_id = await client.resolve_channel("123456", None)
        assert channel_id == "123456"

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_name_not_found(self, client, sample_channels):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            return_value=httpx.Response(200, json=sample_channels)
        )
        with pytest.raises(DiscordAPIError, match="Channel 'nonexistent' not found in guild"):
            await client.resolve_channel("nonexistent", "111222333444555666")

    @pytest.mark.asyncio
    async def test_resolve_name_without_guild_id(self, client):
        with pytest.raises(DiscordAPIError, match="guild_id is required"):
            await client.resolve_channel("general", None)


class TestSendMessage:
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_message(self, client, sample_send_response):
        respx.post(f"{BASE}/channels/100/messages").mock(
            return_value=httpx.Response(200, json=sample_send_response)
        )
        result = await client.send_message("100", content="Hello")
        assert result.id == "msg999"

    @respx.mock
    @pytest.mark.asyncio
    async def test_send_message_with_embed(self, client, sample_send_response):
        respx.post(f"{BASE}/channels/100/messages").mock(
            return_value=httpx.Response(200, json=sample_send_response)
        )
        embed = {"title": "Test", "description": "A test embed"}
        result = await client.send_message("100", embed=embed)
        assert result.id == "msg999"


class TestReadMessages:
    @respx.mock
    @pytest.mark.asyncio
    async def test_read_messages(self, client, sample_messages):
        respx.get(f"{BASE}/channels/100/messages").mock(
            return_value=httpx.Response(200, json=sample_messages)
        )
        messages = await client.read_messages("100", limit=10)
        assert len(messages) == 2
        assert messages[0].author.username == "alice"

    @respx.mock
    @pytest.mark.asyncio
    async def test_read_messages_clamps_limit(self, client, sample_messages):
        respx.get(f"{BASE}/channels/100/messages").mock(
            return_value=httpx.Response(200, json=sample_messages)
        )
        messages = await client.read_messages("100", limit=999)
        # Should clamp to 50 in the request
        assert respx.calls[0].request.url.params["limit"] == "50"


class TestContentValidation:
    @pytest.mark.asyncio
    async def test_send_message_content_too_long(self, client):
        with pytest.raises(DiscordAPIError, match="exceeds 2000 characters"):
            await client.send_message("100", content="x" * 2001)


class TestErrorHandling:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit(self, client):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            return_value=httpx.Response(
                429, json={"message": "You are being rate limited.", "retry_after": 1.5}
            )
        )
        with pytest.raises(DiscordAPIError, match="rate limited.*retry_after.*1.5"):
            await client.list_channels("111222333444555666")

    @respx.mock
    @pytest.mark.asyncio
    async def test_permission_error(self, client):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            return_value=httpx.Response(
                403, json={"message": "Missing Access", "code": 50001}
            )
        )
        with pytest.raises(DiscordAPIError, match="Missing Access"):
            await client.list_channels("111222333444555666")

    @respx.mock
    @pytest.mark.asyncio
    async def test_invalid_token(self, client):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            return_value=httpx.Response(
                401, json={"message": "401: Unauthorized", "code": 0}
            )
        )
        with pytest.raises(DiscordAPIError, match="Unauthorized"):
            await client.list_channels("111222333444555666")

    @respx.mock
    @pytest.mark.asyncio
    async def test_network_error(self, client):
        respx.get(f"{BASE}/guilds/111222333444555666/channels").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        with pytest.raises(DiscordAPIError, match="Network error"):
            await client.list_channels("111222333444555666")
