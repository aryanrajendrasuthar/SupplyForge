import uuid

import redis
import sentry_sdk
from flask import Flask, g, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from supplyforge_auth import SessionStore

from app.auth_routes import bp as auth_bp
from app.config import settings
from app.db import create_all_safely, make_session_factory
from app.routes import bp as suppliers_bp


def create_app(redis_client=None) -> Flask:
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    app = Flask(__name__)
    CORS(app, origins=settings.cors_origins, supports_credentials=True)

    engine, session_factory = make_session_factory(settings.database_url)
    create_all_safely(engine)
    app.session_factory = session_factory

    redis_client = redis_client or redis.Redis.from_url(settings.redis_url)
    app.session_store = SessionStore(redis_client)

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=settings.redis_url,
        default_limits=[settings.rate_limit_default],
    )
    # Auth endpoints get the tighter rate limit from the security baseline
    # (10 req/15min) instead of the general per-service default. Must be
    # applied before the blueprint is registered — Blueprint.record() hooks
    # fire at registration time, not retroactively.
    limiter.limit(settings.rate_limit_auth)(auth_bp)

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

    app.register_blueprint(suppliers_bp)
    app.register_blueprint(auth_bp)

    @app.get("/health")
    def health():
        return {"service": settings.service_name, "status": "ok"}

    return app
