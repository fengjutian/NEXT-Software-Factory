"""AI Project Factory — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.security import setup_cors
from app.api.projects import router as projects_router
from app.websocket.manager import ws_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup: run migrations (in production, this is done separately)
    yield
    # Shutdown: close DB connections
    from app.core.database import engine
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

setup_cors(app)

# Register routers
app.include_router(projects_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.websocket("/ws/projects/{project_id}")
async def project_websocket(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time pipeline progress."""
    await ws_manager.connect(project_id, websocket)
    try:
        # Keep connection alive, listen for client messages (if any)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(project_id, websocket)
    except Exception:
        ws_manager.disconnect(project_id, websocket)
