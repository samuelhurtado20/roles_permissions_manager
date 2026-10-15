from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.openai import PromptRequest, PromptResponse
from app.api.deps import get_openai_service

router = APIRouter(prefix="/openai", tags=["openai"])


@router.post("/generate", response_model=PromptResponse)
async def generate(
    request: PromptRequest,
    service=Depends(get_openai_service),
):
    """Send a prompt to OpenAI and return the response."""
    response = await service.generate(request.prompt)
    return PromptResponse(response=response, model=service.client.api_key and "gpt-4o-mini")