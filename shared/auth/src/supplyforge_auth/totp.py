import pyotp


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, account_email: str, issuer: str = "SupplyForge") -> str:
    """URI for QR-code enrollment in an authenticator app."""
    return pyotp.TOTP(secret).provisioning_uri(name=account_email, issuer_name=issuer)


def verify_totp_code(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
