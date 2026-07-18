import sentry_sdk
from flask import Flask
from flask_cors import CORS

from app.config import settings


def create_app() -> Flask:
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    app = Flask(__name__)
    CORS(app, origins=settings.cors_origins, supports_credentials=True)

    @app.get("/health")
    def health():
        return {"service": settings.service_name, "status": "ok"}

    return app
