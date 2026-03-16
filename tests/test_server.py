import json
from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp.types import Channel, Message, MessageAuthor, SendResult
from discord_mcp.server import resolve_guild_id, handle_list_channels, handle_send_message, handle_read_messages, handle_send_embed


class TestResolveGuildId:
    def test_explicit_guild_id(self):
        assert resolve_guild_id("123") == "123"

    @patch.dict("os.environ", {"DISCORD_DEFAULT_GUILD_ID": "default999"})
    def test_fallback_to_env(self):
        assert resolve_guild_id(None) == "default999"

    @patch.dict("os.environ", {}, clear=True)
    def test_none_when_no_default(self):
        assert resolve_guild_id(None) is None


class TestHandleListChannels:
    @pytest.mark.asyncio
    async def test_list_channels(self):
        mock_client = AsyncMock()
        mock_client.list_channels.return_value = [
            Channel(id="100", name="general", type=0, topic="Chat"),
            Channel(id="101", name="random", type=0),
        ]
        result = await handle_list_channels(mock_client, guild_id="guild1")
        assert len(result) == 2
        assert result[0]["name"] == "general"
        assert result[0]["topic"] == "Chat"
        assert result[0]["category"] is None


class TestHandleSendMessage:
    @pytest.mark.asyncio
    async def test_send_plain_message(self):
        mock_client = AsyncMock()
        mock_client.resolve_channel.return_value = "100"
        mock_client.send_message.return_value = SendResult(
            id="msg1", timestamp="2026-03-15T12:00:00+00:00"
        )
        result = await handle_send_message(
            mock_client, channel="general", guild_id="guild1", content="Hello"
        )
        assert result["message_id"] == "msg1"
        mock_client.send_message.assert_called_once_with("100", content="Hello", embed=None)


class TestHandleReadMessages:
    @pytest.mark.asyncio
    async def test_read_messages(self):
        mock_client = AsyncMock()
        mock_client.resolve_channel.return_value = "100"
        mock_client.read_messages.return_value = [
            Message(
                id="m1",
                author=MessageAuthor(id="u1", username="alice"),
                content="Hi",
                timestamp="2026-03-15T10:00:00+00:00",
            ),
        ]
        result = await handle_read_messages(
            mock_client, channel="100", guild_id=None, limit=10
        )
        assert len(result) == 1
        assert result[0]["author"] == "alice"
        assert result[0]["content"] == "Hi"


class TestHandleSendEmbed:
    @pytest.mark.asyncio
    async def test_send_embed(self):
        mock_client = AsyncMock()
        mock_client.resolve_channel.return_value = "100"
        mock_client.send_message.return_value = SendResult(
            id="msg2", timestamp="2026-03-15T12:00:00+00:00"
        )
        result = await handle_send_embed(
            mock_client,
            channel="general",
            guild_id="guild1",
            title="Deploy",
            description="Deployed v1.2",
            color=3447003,
            fields=[{"name": "Status", "value": "OK", "inline": True}],
            content=None,
        )
        assert result["message_id"] == "msg2"
        call_args = mock_client.send_message.call_args
        embed_arg = call_args.kwargs.get("embed") or call_args[1].get("embed")
        assert embed_arg["title"] == "Deploy"
        assert embed_arg["color"] == 3447003
