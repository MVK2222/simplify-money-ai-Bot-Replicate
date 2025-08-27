# core/chat_flow.py
import logging
from core.prompts import build_gemini_prompt, build_chatbot_prompt
from services.gemini_client import call_gemini_api
from core.chat_manager import add_to_history, get_history
from services.gold_price import get_live_gold_price
from sqlmodel import Session
from routers.gold_purchase import (
    kyc_step,
    quantity_step,
    payment_step,
    vault_step,
    receipt_step,
)


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
        for turn in history[-5:]:  # last 10 exchanges for context
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
        chatbot_prompt = build_chatbot_prompt(user_query, history)
        result = await call_gemini_api(chatbot_prompt)
        stage = result.get("stage", "exploration")

        # Step 3: Simulate gold purchase API calls based on stage
        if stage == "buy_step_1":
            resp = kyc_step(
                {"user_id": int(user_id), "kyc_details": "Dummy KYC"}, session
            )
            result["answer"] += f" ✅ KYC done. Next: {resp['next_endpoint']}"
            result["buy_link"] = resp["next_endpoint"]

        elif stage == "buy_step_2":
            # Use live gold price if available
            grams, amount = 1.0, None  # example default, could be dynamic
            resp = quantity_step(
                {"user_id": int(user_id), "grams": grams, "amount": amount}, session
            )
            result["answer"] += f" ✅ Quantity set. Next: {resp['next_endpoint']}"
            result["buy_link"] = resp["next_endpoint"]

        elif stage == "buy_step_3":
            resp = payment_step(
                {"user_id": int(user_id), "payment_method": "UPI", "amount": 5000},
                session,
            )
            result["answer"] += f" ✅ Payment confirmed. Next: {resp['next_endpoint']}"
            result["buy_link"] = resp["next_endpoint"]

        elif stage == "buy_step_4":
            resp = vault_step({"user_id": int(user_id), "confirm": True}, session)
            result["answer"] += f" ✅ Vault confirmed. Next: {resp['next_endpoint']}"
            result["buy_link"] = resp["next_endpoint"]

        elif stage == "buy_step_5":
            resp = receipt_step({"user_id": int(user_id)}, session)
            result["answer"] += f" ✅ Purchase complete. Receipt generated."
            result["buy_link"] = ""

    else:
        # For other intents, just return Gemini’s answer
        result = intent_response
        # Save assistant response
    add_to_history(user_id, "assistant", result.get("answer", ""))

    return result
