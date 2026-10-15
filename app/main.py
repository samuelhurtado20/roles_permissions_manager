from fastapi import FastAPI
from app.core.config import settings
from app.api.routes.users import router as users_router
from app.api.routes.openai import router as openai_router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG,
)

# Include routers
app.include_router(users_router)
app.include_router(openai_router)


@app.get("/")
async def root():
    return {"message": "Hello World", "app": settings.APP_NAME}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}