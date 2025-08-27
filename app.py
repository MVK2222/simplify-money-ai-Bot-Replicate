### app.py
from fastapi import FastAPI
from routers import auth
from database.db import init_db

# from routers import ask
from routers import chat, gold_purchase


def create_app():
    app = FastAPI(title="Simplify AI Assignment")
    init_db()
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(chat.router, prefix="", tags=["Chats"])
    app.include_router(gold_purchase.router)

    return app
