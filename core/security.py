### core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
import logging


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "change_this_secret_for_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def hash_password(password: str) -> str:
    logger.debug("Hashing password.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Verifying password.")
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    logger.info(f"Creating access token for: {data}")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
