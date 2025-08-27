# core/chat_flow.py
import logging
from core.prompts import build_gemini_prompt, build_chatbot_prompt
from services.gemini_client import call_gemini_api
from core.chat_manager import add_to_history, get_history
from services.gold_price import get_live_gold_price
from database.db import get_session
from database.models import GoldOrder
from sqlmodel import Session


async def process_user_query(user_id: str, user_query: str, session: Session) -> dict:
    """
    Process a user query:
    1. Detect intent using Gemini.
    2. If intent is 'ready_to_invest', use stepwise chatbot prompt with embedded endpoints.
    3. Save the responses to conversation history.
    """

    logging.info(f"[DEBUG] Processing query for user {user_id}: {user_query}")

    # Add user query to history
    add_to_history(user_id, "user", user_query)
    history = get_history(user_id)

    # Helper: format conversation history into string
    def format_history(history: list) -> str:
        chat_text = ""
        for turn in history[-10:]:  # last 10 exchanges for context
            role = "User" if turn["role"] == "user" else "Assistant"
            chat_text += f"{role}: {turn['content']}\n"
        return chat_text

    chat_text = format_history(history)

    # 🔹 Safe gold price fetch
    live_price = None
    if "gold" in user_query.lower():
        try:
            live_price = await get_live_gold_price()
        except Exception as e:
            logging.error(f"[ERROR] Failed to fetch gold price: {e}")
            live_price = None

        if live_price:
            chat_text += f"\n[System]: The current live gold price is {live_price} INR per gram. Use this for all calculations and advice.\n"
        else:
            chat_text += "\n[System]: Gold price is currently unavailable. Do not guess, just explain general strategies.\n"

    # Step 1: Intent detection using Gemini
    intent_prompt = build_gemini_prompt(user_query)
    intent_response = await call_gemini_api(intent_prompt)
    intent = intent_response.get("intent", "irrelevant")
    logging.info(f"[DEBUG] Detected intent: {intent}")

    # Step 2: If ready_to_invest, switch to chatbot prompt
    if intent == "ready_to_invest":
        logging.info(
            f"[DEBUG] Using chatbot prompt for stepwise gold purchase for user {user_id}"
        )
        chatbot_prompt = build_chatbot_prompt(user_query, history)
        result = await call_gemini_api(chatbot_prompt)

        # Save step to DB if stage corresponds to a gold purchase step
        stage = result.get("stage")
        if stage in [
            "ready_to_buy",
            "buy_step_1",
            "buy_step_2",
            "buy_step_3",
            "buy_step_4",
            "buy_step_5",
        ]:
            order = GoldOrder(
                user_id=user_id,
                step=stage.upper(),
                amount=result.get("meta", {}).get("amount"),
                payment_method=result.get("meta", {}).get("payment_method"),
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            result["order_id"] = order.id

        # Provide next action link from Gemini
        result["buy_link"] = result.get("buy_link", "")

    else:
        logging.info(f"[DEBUG] Using intent response for user {user_id}")
        result = intent_response

    # Save assistant response to history
    add_to_history(user_id, "assistant", result.get("answer", ""))

    return result
