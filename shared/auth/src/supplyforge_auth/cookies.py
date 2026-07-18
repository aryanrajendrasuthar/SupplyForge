from typing import Protocol


class _SupportsSetCookie(Protocol):
    def set_cookie(self, key: str, value: str, **kwargs: object) -> None: ...


SESSION_COOKIE_NAME = "sf_session"


def set_session_cookie(response: _SupportsSetCookie, token: str, max_age_seconds: int) -> None:
    """Sets the session cookie with the flags every service must use: HttpOnly,
    Secure, SameSite=Strict. Never set this cookie manually in a service."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=max_age_seconds,
        httponly=True,
        secure=True,
        samesite="Strict",
    )


def clear_session_cookie(response: _SupportsSetCookie) -> None:
    response.set_cookie(SESSION_COOKIE_NAME, "", max_age=0, httponly=True, secure=True, samesite="Strict")
