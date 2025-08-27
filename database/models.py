from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        logger.debug(f"User __repr__ called for: {self.email}")
        return f"<User id={self.id} email={self.email}>"


class GoldOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    step: str  # KYC, QUANTITY, PAYMENT, VAULT_CONFIRM, POST_BUY
    payment_method: Optional[str] = None
    amount: Optional[float] = None
    quantity_grams: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        logger.debug(
            f"GoldOrder __repr__ called for user_id: {self.user_id}, step: {self.step}"
        )
        return f"<GoldOrder id={self.id} user_id={self.user_id} step={self.step}>"
