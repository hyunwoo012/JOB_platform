from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional
from ..deps import get_async_db, get_current_user, get_current_user_optional
from ..models import User
from ..schemas import ChatbotRequest, ChatbotResponse
from ..services.chatbot_services import chatbot

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/chat", response_model=ChatbotResponse)
async def chat_with_bot(
        payload: ChatbotRequest,
        user: Optional[User] = Depends(get_current_user_optional),
):
    """
    rule based chatbot
    """
    message = payload.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="메시지를 입력해주세요")

    # Create a chatbot response
    reply = chatbot.get_response(message)

    return ChatbotResponse(
        reply=reply,
        source="rule_based"
    )


@router.get("/intents")
async def get_available_intents(
        user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List of topics that chatbots can understand
    """
    return {
        "intents": [
        { "name": "Greeting", "examples": ["hi", "hello", "hey"] },
        { "name": "Job Search", "examples": ["job", "part-time", "hiring"] },
        { "name": "Application Guide", "examples": ["apply", "application", "how"] },
        { "name": "Wage Information", "examples": ["wage", "pay", "salary"] },
        { "name": "Profile", "examples": ["profile", "resume", "information"] },
        { "name": "Help", "examples": ["help", "support", "question"] }
        ]

    }