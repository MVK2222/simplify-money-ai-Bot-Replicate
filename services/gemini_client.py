import json
import logging
import google.generativeai as genai
from core.chat_manager import get_history, add_to_history
from core.prompts import build_gemini_prompt, build_chatbot_prompt
from services.gold_price import get_live_gold_price


async def call_gemini_api(prompt: str) -> dict:
    """
    Call Gemini API via official SDK and return parsed JSON response.
    """
    try:
        genai.configure(api_key="AIzaSyApn7kcgtCyFrfz_j_2vwpwVdHTIuIy7lo")
        # genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        logging.info("Gemini AI initialized for enhanced detection")
        response = model.generate_content(prompt)

        # Modern SDK: response.text gives the text output
        content = getattr(response, "text", "")

        # Try parsing JSON from the LLM
        try:
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError:
            # Fallback minimal JSON
            return {
                "query": "",
                "source": "gemini",
                "category": "irrelevant",
                "answer": content,
                "meta": {"confidence": 0.0},
            }

    except Exception as e:
        return {
            "query": "",
            "source": "gemini",
            "category": "irrelevant",
            "answer": f"Error contacting Gemini SDK: {str(e)}",
            "meta": {"confidence": 0.0},
        }
