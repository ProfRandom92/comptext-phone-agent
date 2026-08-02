from __future__ import annotations
import secrets
from fastapi import FastAPI
from .routes import router

def create_app(context) -> FastAPI:
    app = FastAPI(title="CompText Phone Agent", docs_url="/docs")
    app.state.session_token = secrets.token_urlsafe(32)
    app.state.csrf_token = secrets.token_urlsafe(32)
    app.state.config = context.config
    app.state.data_dir = context.data_dir
    app.state.database = context.database
    app.state.audit = context.audit
    app.state.trash = context.trash
    app.state.scanner = context.scanner
    app.include_router(router)
    return app
