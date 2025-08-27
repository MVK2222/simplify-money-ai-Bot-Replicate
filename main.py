from uvicorn import run
from app import create_app
import logging

logging.basicConfig(level=logging.INFO)

app = create_app()


if __name__ == "__main__":
    logging.info("Starting Uvicorn server...")
    run("main:app", host="127.0.0.1", port=8000, reload=True)
