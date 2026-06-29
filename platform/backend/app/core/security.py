"""Security and CORS middleware configuration."""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.core.config import get_settings


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware."""
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
