import sentry_sdk
from ariadne import graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import settings
from app.schema import schema

_explorer_html = ExplorerGraphiQL().html(None)


def create_app() -> Flask:
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    app = Flask(__name__)
    CORS(app, origins=settings.cors_origins, supports_credentials=True)

    Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=settings.redis_url,
        default_limits=[settings.rate_limit_default],
    )

    @app.get("/graphql")
    def graphql_explorer():
        return _explorer_html, 200

    @app.post("/graphql")
    def graphql_server():
        success, result = graphql_sync(
            schema, request.get_json(), context_value=request, debug=app.debug
        )
        return jsonify(result), 200 if success else 400

    @app.get("/health")
    def health():
        return {"service": settings.service_name, "status": "ok"}

    return app
