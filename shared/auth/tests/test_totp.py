import pyotp

from supplyforge_auth import generate_totp_secret, provisioning_uri, verify_totp_code


def test_secret_is_valid_base32():
    secret = generate_totp_secret()
    assert len(secret) == 32


def test_verify_accepts_current_code():
    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp_code(secret, code) is True


def test_verify_rejects_wrong_code():
    secret = generate_totp_secret()
    assert verify_totp_code(secret, "000000") is False


def test_provisioning_uri_includes_issuer_and_account():
    secret = generate_totp_secret()
    uri = provisioning_uri(secret, "user@example.com")
    assert "SupplyForge" in uri
    assert "user%40example.com" in uri
