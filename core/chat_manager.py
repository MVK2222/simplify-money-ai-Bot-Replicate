# core/chat_manager.py
from typing import Dict, List

# Simple in-memory storage: { user_id: [ {"role": "user/assistant", "content": "..."} ] }
chat_histories: Dict[str, List[Dict[str, str]]] = {}


def get_history(user_id: str) -> List[Dict[str, str]]:
    return chat_histories.get(user_id, [])


def add_to_history(user_id: str, role: str, content: str):
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    chat_histories[user_id].append({"role": role, "content": content})


def clear_history(user_id: str):
    chat_histories[user_id] = []
