from fastapi import APIRouter, Query, Depends
from sqlmodel import Session
from database.db import get_session
from core.chat_flow import process_user_query
from core.chat_manager import clear_history

router = APIRouter()


@router.post("/chat")
async def chat(
    user_id: str = Query(...),
    query: str = Query(...),
    session: Session = Depends(get_session),  # <-- inject DB session
):
    """
    Chat endpoint with history support.
    """
    response = await process_user_query(user_id, query, session)  # pass session here
    return response


@router.post("/chat/clear")
async def clear_chat(user_id: str = Query(...)):
    """
    Clear conversation history for a user.
    """
    clear_history(user_id)
    return {"message": f"Chat history cleared for user {user_id}"}
