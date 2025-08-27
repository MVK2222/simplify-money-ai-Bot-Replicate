from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import Optional
from pydantic import BaseModel
from database.db import get_session
from database.models import User, GoldOrder
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gold", tags=["Gold Purchase"])


# ----- Request Schemas -----
class KYCRequest(BaseModel):
    user_id: int
    kyc_details: str  # dummy field


class QuantityRequest(BaseModel):
    user_id: int
    grams: Optional[float] = None
    amount: Optional[float] = None


class PaymentRequest(BaseModel):
    user_id: int
    payment_method: str
    amount: float


class VaultRequest(BaseModel):
    user_id: int
    confirm: bool


class ReceiptRequest(BaseModel):
    user_id: int


# ----- Step 1: KYC -----
@router.post("/kyc")
def kyc_step(req: KYCRequest, session: Session = Depends(get_session)):
    order = GoldOrder(user_id=req.user_id, step="KYC")
    session.add(order)
    session.commit()
    session.refresh(order)
    return {
        "message": "KYC completed ✅",
        "next_endpoint": "/api/gold/quantity",
        "order_id": order.id,
    }


# ----- Step 2: Choose Quantity or Amount -----
@router.post("/quantity")
def quantity_step(req: QuantityRequest, session: Session = Depends(get_session)):
    order = GoldOrder(
        user_id=req.user_id,
        step="QUANTITY",
        quantity_grams=req.grams,
        amount=req.amount,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return {
        "message": f"Quantity set: {req.grams} grams / ₹{req.amount}",
        "next_endpoint": "/api/gold/payment",
        "order_id": order.id,
    }


# ----- Step 3: Payment -----
@router.post("/payment")
def payment_step(req: PaymentRequest, session: Session = Depends(get_session)):
    order = GoldOrder(
        user_id=req.user_id,
        step="PAYMENT",
        payment_method=req.payment_method,
        amount=req.amount,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return {
        "message": f"Payment of ₹{req.amount} via {req.payment_method} confirmed ✅",
        "next_endpoint": "/api/gold/vault",
        "order_id": order.id,
    }


# ----- Step 4: Vault / Storage Confirm -----
@router.post("/vault")
def vault_step(req: VaultRequest, session: Session = Depends(get_session)):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Vault confirmation required")
    order = GoldOrder(user_id=req.user_id, step="VAULT_CONFIRM")
    session.add(order)
    session.commit()
    session.refresh(order)
    return {
        "message": "Vault storage confirmed ✅",
        "next_endpoint": "/api/gold/receipt",
        "order_id": order.id,
    }


# ----- Step 5: Receipt -----
@router.post("/receipt")
def receipt_step(req: ReceiptRequest, session: Session = Depends(get_session)):
    order = GoldOrder(user_id=req.user_id, step="POST_BUY")
    session.add(order)
    session.commit()
    session.refresh(order)
    return {"message": "Purchase complete 🎉 Receipt generated", "order_id": order.id}
