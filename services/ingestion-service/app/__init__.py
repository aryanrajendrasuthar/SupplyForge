import uuid

import sentry_sdk
from flask import Flask, g, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import settings
from app.db import make_records_collection
from app.events import SqsEventPublisher, make_sqs_client
from app.routes import bp as ingestion_bp


def create_app(records_collection=None) -> Flask:
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    app = Flask(__name__)
    CORS(app, origins=settings.cors_origins, supports_credentials=True)

    app.records_collection = records_collection or make_records_collection(
        settings.mongo_url, settings.mongo_db_name
    )
    app.event_publisher = SqsEventPublisher(
        make_sqs_client(settings.sqs_endpoint_url), settings.ai_validation_queue_url
    )

    Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=settings.redis_url,
        default_limits=[settings.rate_limit_default],
    )

    @app.before_request
    def _start_request():
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        g.records = app.records_collection

    @app.after_request
    def _add_correlation_header(response):
        response.headers["X-Correlation-ID"] = g.get("correlation_id", "")
        return response

    app.register_blueprint(ingestion_bp)

    @app.get("/health")
    def health():
        return {"service": settings.service_name, "status": "ok"}

    return app
