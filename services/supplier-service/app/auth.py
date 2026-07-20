from sqlalchemy import select
from sqlalchemy.orm import Session
from supplyforge_auth import hash_password, verify_password, verify_totp_code

from app.models import User


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class TotpRequiredError(Exception):
    pass


def register_user(db: Session, email: str, password: str, role: str) -> User:
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise EmailAlreadyRegisteredError(f"'{email}' is already registered")

    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str, totp_code: str | None) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("invalid email or password")

    if user.totp_secret:
        if not totp_code:
            raise TotpRequiredError("TOTP code required")
        if not verify_totp_code(user.totp_secret, totp_code):
            raise InvalidCredentialsError("invalid TOTP code")

    return user
