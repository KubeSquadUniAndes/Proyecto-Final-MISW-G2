from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class RefreshToken:
    user_id: UUID
    token: str
    expires_at: datetime
    id: UUID = field(default_factory=uuid4)
    revoked: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def revoke(self) -> None:
        self.revoked = True

    def is_valid(self) -> bool:
        return not self.revoked and datetime.now(timezone.utc) < self.expires_at
