from pydantic import BaseModel, field_validator, model_validator

# Discord API limits
MAX_MESSAGE_CONTENT = 2000
MAX_EMBED_TITLE = 256
MAX_EMBED_DESCRIPTION = 4096
MAX_EMBED_FIELDS = 25
MAX_EMBED_FIELD_NAME = 256
MAX_EMBED_FIELD_VALUE = 1024
MAX_EMBED_TOTAL = 6000


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

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        if len(v) > MAX_EMBED_FIELD_NAME:
            raise ValueError(f"Field name exceeds {MAX_EMBED_FIELD_NAME} characters")
        return v

    @field_validator("value")
    @classmethod
    def value_length(cls, v: str) -> str:
        if len(v) > MAX_EMBED_FIELD_VALUE:
            raise ValueError(f"Field value exceeds {MAX_EMBED_FIELD_VALUE} characters")
        return v


class Embed(BaseModel):
    title: str
    description: str | None = None
    color: int | None = None
    fields: list[EmbedField] = []

    @field_validator("title")
    @classmethod
    def title_length(cls, v: str) -> str:
        if len(v) > MAX_EMBED_TITLE:
            raise ValueError(f"Embed title exceeds {MAX_EMBED_TITLE} characters")
        return v

    @field_validator("description")
    @classmethod
    def description_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) > MAX_EMBED_DESCRIPTION:
            raise ValueError(f"Embed description exceeds {MAX_EMBED_DESCRIPTION} characters")
        return v

    @field_validator("fields")
    @classmethod
    def fields_count(cls, v: list[EmbedField]) -> list[EmbedField]:
        if len(v) > MAX_EMBED_FIELDS:
            raise ValueError(f"Embed exceeds maximum of {MAX_EMBED_FIELDS} fields")
        return v

    @model_validator(mode="after")
    def total_length(self) -> "Embed":
        total = len(self.title)
        if self.description:
            total += len(self.description)
        for f in self.fields:
            total += len(f.name) + len(f.value)
        if total > MAX_EMBED_TOTAL:
            raise ValueError(f"Embed total content exceeds {MAX_EMBED_TOTAL} characters")
        return self
