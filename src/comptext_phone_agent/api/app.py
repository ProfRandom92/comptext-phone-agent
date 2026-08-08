from __future__ import annotations
import secrets
from starlette.applications import Starlette
from .routes import routes


def create_app(context) -> Starlette:
    app = Starlette(debug=False, routes=routes)
    app.state.session_token = secrets.token_urlsafe(32)
    app.state.csrf_token = secrets.token_urlsafe(32)
    app.state.config = context.config
    app.state.data_dir = context.data_dir
    app.state.database = context.database
    app.state.audit = context.audit
    app.state.trash = context.trash
    app.state.scanner = context.scanner
    return app
