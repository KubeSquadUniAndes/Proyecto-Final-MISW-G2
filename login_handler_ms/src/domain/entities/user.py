from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class UserStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    INACTIVE = "inactive"


@dataclass
class User:
    email: str
    hashed_password: str
    id: UUID = field(default_factory=uuid4)
    full_name: str | None = None
    status: UserStatus = UserStatus.ACTIVE
    is_superuser: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def block(self, reason: str | None = None) -> None:
        if self.status == UserStatus.BLOCKED:
            raise ValueError("User is already blocked")
        self.status = UserStatus.BLOCKED
        self.updated_at = datetime.utcnow()

    def unblock(self) -> None:
        if self.status != UserStatus.BLOCKED:
            raise ValueError("User is not blocked")
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def is_blocked(self) -> bool:
        return self.status == UserStatus.BLOCKED
