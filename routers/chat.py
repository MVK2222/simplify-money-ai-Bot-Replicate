# routes/chat.py
from fastapi import APIRouter, Query
from core.chat_flow import process_user_query
from core.chat_manager import clear_history

router = APIRouter()


@router.post("/chat")
async def chat(user_id: str = Query(...), query: str = Query(...)):
    """
    Chat endpoint with history support.
    """
    response = await process_user_query(user_id, query)
    return response


@router.post("/chat/clear")
async def clear_chat(user_id: str = Query(...)):
    """
    Clear conversation history for a user.
    """
    clear_history(user_id)
    return {"message": f"Chat history cleared for user {user_id}"}
