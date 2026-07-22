class Notifier:
    """Sends customer-facing order notifications (confirmation, cancellation,
    shipping, delivery). No real email provider is wired — that would need
    SMTP/SendGrid credentials, the same stated tradeoff as Groq/Sentry (see
    docs/project-plan.md §1) — so this logs what would be sent rather than
    silently doing nothing."""

    def send(self, to: str, subject: str, body: str) -> None:
        print(f"[notification] to={to} subject={subject!r} body={body!r}")
