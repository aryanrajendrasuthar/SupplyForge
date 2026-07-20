from flask import Blueprint, current_app, g, jsonify, request
from pydantic import ValidationError
from supplyforge_auth import clear_session_cookie, require_session, set_session_cookie
from supplyforge_auth.cookies import SESSION_COOKIE_NAME

from app.auth import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    TotpRequiredError,
    authenticate_user,
    register_user,
)
from app.schemas import UserLogin, UserRegister

bp = Blueprint("auth", __name__, url_prefix="/auth")

SESSION_TTL_SECONDS = 12 * 60 * 60


@bp.post("/register")
def register():
    try:
        payload = UserRegister.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    try:
        user = register_user(g.db, payload.email, payload.password, payload.role)
    except EmailAlreadyRegisteredError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify({"id": user.id, "email": user.email, "role": user.role}), 201


@bp.post("/login")
def login():
    try:
        payload = UserLogin.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    try:
        user = authenticate_user(g.db, payload.email, payload.password, payload.totp_code)
    except (TotpRequiredError, InvalidCredentialsError) as exc:
        return jsonify({"error": str(exc)}), 401

    token = current_app.session_store.create({"user_id": str(user.id), "email": user.email, "role": user.role})
    response = jsonify({"id": user.id, "email": user.email, "role": user.role})
    set_session_cookie(response, token, SESSION_TTL_SECONDS)
    return response, 200


@bp.post("/logout")
@require_session()
def logout():
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        current_app.session_store.revoke(token)
    response = jsonify({"status": "logged out"})
    clear_session_cookie(response)
    return response, 200
