from sqlmodel import SQLModel, create_engine, Session
import logging

DATABASE_URL = "sqlite:///./dev.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def init_db():
    """Initialize database and create tables if they do not exist."""
    logger.info("Initializing database and creating tables...")
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a DB session generator for dependency injection."""
    logger.debug("Creating new DB session.")
    with Session(engine) as session:
        yield session
