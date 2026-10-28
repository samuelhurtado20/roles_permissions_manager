from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.users import router as users_router
from app.api.routes.openai import router as openai_router
from app.api.routes.roles import router as roles_router
from app.api.routes.permissions import router as permissions_router
from app.api.routes.chat import router as chat_router
from app.utils.errors import ErrorHandlingMiddleware
from app.utils.metrics import MetricsMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.APP_DEBUG,
        version="1.0.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(MetricsMiddleware)

    # Include routers
    app.include_router(users_router)
    app.include_router(openai_router)
    app.include_router(roles_router)
    app.include_router(permissions_router)
    app.include_router(chat_router)

    @app.get("/")
    async def root():
        return {"message": "Hello World", "app": settings.APP_NAME}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()