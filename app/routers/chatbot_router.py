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
        user: User = Depends(get_current_user),
):
    """
    List of topics that chatbots can understand
    """
    return {
        "intents": [
            {"name": "인사", "examples": ["안녕", "hi", "hello"]},
            {"name": "일자리 검색", "examples": ["알바", "구인", "공고"]},
            {"name": "지원 방법", "examples": ["지원", "신청", "방법"]},
            {"name": "급여 정보", "examples": ["급여", "시급", "얼마"]},
            {"name": "프로필", "examples": ["프로필", "이력서", "정보"]},
            {"name": "도움말", "examples": ["도움", "help", "문의"]},
        ]
    }