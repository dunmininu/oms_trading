from typing import List, Optional
from datetime import datetime
from ninja import Schema

class CreateApiKeyIn(Schema):
    name: str
    scopes: List[str]
    expires_at: Optional[datetime] = None