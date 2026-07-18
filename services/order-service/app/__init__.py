import uuid

import sentry_sdk
from flask import Flask, g, request
from flask_cors import CORS

from app.config import settings
from app.db import Base, make_session_factory
from app.events import SqsEventPublisher, make_sqs_client
from app.routes import bp as orders_bp


def create_app() -> Flask:
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    app = Flask(__name__)
    CORS(app, origins=settings.cors_origins, supports_credentials=True)

    engine, session_factory = make_session_factory(settings.database_url)
    Base.metadata.create_all(engine)
    app.session_factory = session_factory
    app.event_publisher = SqsEventPublisher(
        make_sqs_client(settings.sqs_endpoint_url), settings.reservation_queue_url
    )

    @app.before_request
    def _start_request():
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        g.db = session_factory()

    @app.teardown_appcontext
    def _end_request(exception=None):
        session_factory.remove()

    @app.after_request
    def _add_correlation_header(response):
        response.headers["X-Correlation-ID"] = g.get("correlation_id", "")
        return response

    app.register_blueprint(orders_bp)

    @app.get("/health")
    def health():
        return {"service": settings.service_name, "status": "ok"}

    return app
