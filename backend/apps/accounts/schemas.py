from datetime import datetime

from ninja import Schema


class CreateApiKeyIn(Schema):
    name: str
    scopes: list[str]
    expires_at: datetime | None = None
