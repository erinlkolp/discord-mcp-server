from discord_mcp.types import Channel, Message, MessageAuthor, SendResult, Embed, EmbedField


class TestChannel:
    def test_parse_full_channel(self):
        data = {
            "id": "123456",
            "name": "general",
            "topic": "General discussion",
            "type": 0,
            "parent_id": "999",
        }
        ch = Channel(**data)
        assert ch.id == "123456"
        assert ch.name == "general"
        assert ch.topic == "General discussion"
        assert ch.type == 0
        assert ch.parent_id == "999"

    def test_parse_channel_missing_optional_fields(self):
        data = {"id": "123", "name": "test", "type": 0}
        ch = Channel(**data)
        assert ch.topic is None
        assert ch.parent_id is None


class TestMessage:
    def test_parse_message(self):
        data = {
            "id": "msg1",
            "author": {"id": "user1", "username": "alice"},
            "content": "Hello world",
            "timestamp": "2026-03-15T10:00:00+00:00",
        }
        msg = Message(**data)
        assert msg.id == "msg1"
        assert msg.author.username == "alice"
        assert msg.content == "Hello world"

    def test_parse_message_empty_content(self):
        data = {
            "id": "msg2",
            "author": {"id": "user1", "username": "bob"},
            "content": "",
            "timestamp": "2026-03-15T10:00:00+00:00",
        }
        msg = Message(**data)
        assert msg.content == ""


class TestSendResult:
    def test_parse_send_result(self):
        data = {"id": "msg123", "timestamp": "2026-03-15T12:00:00+00:00"}
        result = SendResult(**data)
        assert result.id == "msg123"


class TestEmbed:
    def test_embed_with_fields(self):
        embed = Embed(
            title="Status",
            description="All systems go",
            color=3447003,
            fields=[EmbedField(name="Uptime", value="99.9%", inline=True)],
        )
        assert embed.title == "Status"
        assert len(embed.fields) == 1
        assert embed.fields[0].inline is True

    def test_embed_minimal(self):
        embed = Embed(title="Hello")
        assert embed.description is None
        assert embed.color is None
        assert embed.fields == []
