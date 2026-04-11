from abc import ABC, abstractmethod


class PasswordServicePort(ABC):
    """Output port: password hashing abstraction (keeps domain free of bcrypt)."""

    @abstractmethod
    def hash(self, plain_password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...
