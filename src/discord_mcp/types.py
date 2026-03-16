from pydantic import BaseModel


class Channel(BaseModel):
    id: str
    name: str
    type: int
    topic: str | None = None
    parent_id: str | None = None
    category_name: str | None = None  # Resolved from parent_id by DiscordClient


class MessageAuthor(BaseModel):
    id: str
    username: str


class Message(BaseModel):
    id: str
    author: MessageAuthor
    content: str
    timestamp: str


class SendResult(BaseModel):
    id: str
    timestamp: str


class EmbedField(BaseModel):
    name: str
    value: str
    inline: bool = False


class Embed(BaseModel):
    title: str
    description: str | None = None
    color: int | None = None
    fields: list[EmbedField] = []
