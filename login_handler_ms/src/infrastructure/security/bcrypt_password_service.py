import bcrypt

from src.domain.services.password_service_port import PasswordServicePort


class BcryptPasswordService(PasswordServicePort):
    """Output adapter: password hashing using bcrypt."""

    def hash(self, plain_password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain_password.encode(), salt).decode()

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
