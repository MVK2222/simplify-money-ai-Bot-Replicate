### README.md
# Simplify AI Assignment - Module 1 (Auth + DB)


## Overview
This module implements:
- FastAPI backend skeleton
- SQLite (SQLModel) DB
- Signup and Login endpoints with JWT
- Unit tests for auth


## Run locally
1. Create virtualenv and install deps:
```bash
python -m venv .venv
source .venv/bin/activate # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```
2. Start the server:
```bash
uvicorn main:app --reload
```
Swagger UI: http://127.0.0.1:8000/docs


3. Run tests:
```bash
pytest -q
```


---