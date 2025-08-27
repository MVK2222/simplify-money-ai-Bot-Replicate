# routers/gold_purchase.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from database.db import get_session
from database.models import User, GoldOrder
from services.gold_price import get_live_gold_price  # assumes you have this function

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gold", tags=["gold_purchase"])


# ---------------- Request Schemas ----------------
class KYCRequest(BaseModel):
    user_id: int
    kyc_details: str  # basic details: name, email, phone


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


# ---------------- Step 1: KYC ----------------
@router.post("/kyc")
def kyc_step(req: KYCRequest, session: Session = Depends(get_session)):
    if not req.kyc_details.strip():
        raise HTTPException(status_code=400, detail="KYC details cannot be empty")

    order = GoldOrder(user_id=req.user_id, step="KYC", kyc_details=req.kyc_details)
    session.add(order)
    session.commit()
    session.refresh(order)
    return {
        "message": "KYC completed ✅",
        "next_endpoint": "/api/gold/quantity",
        "order_id": order.id,
    }


# ---------------- Step 2: Quantity / Amount ----------------
@router.post("/quantity")
def quantity_step(req: QuantityRequest, session: Session = Depends(get_session)):
    gold_price = get_live_gold_price()  # INR per gram
    if not gold_price:
        raise HTTPException(status_code=500, detail="Gold price unavailable")

    if req.grams and not req.amount:
        req.amount = round(req.grams * gold_price, 2)
    elif req.amount and not req.grams:
        req.grams = round(req.amount / gold_price, 4)
    elif not req.amount and not req.grams:
        raise HTTPException(status_code=400, detail="Provide grams or amount")

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


# ---------------- Step 3: Payment ----------------
@router.post("/payment")
def payment_step(req: PaymentRequest, session: Session = Depends(get_session)):
    last_order = session.exec(
        f"SELECT * FROM goldorder WHERE user_id={req.user_id} ORDER BY id DESC LIMIT 1"
    ).first()

    if not last_order or last_order.step != "QUANTITY":
        raise HTTPException(
            status_code=400, detail="Quantity step must be completed first"
        )

    if req.amount != last_order.amount:
        raise HTTPException(status_code=400, detail="Payment amount mismatch")

    transaction_id = str(uuid.uuid4())
    order = GoldOrder(
        user_id=req.user_id,
        step="PAYMENT",
        payment_method=req.payment_method,
        amount=req.amount,
        transaction_id=transaction_id,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return {
        "message": f"Payment of ₹{req.amount} via {req.payment_method} confirmed ✅",
        "transaction_id": transaction_id,
        "next_endpoint": "/api/gold/vault",
        "order_id": order.id,
    }


# ---------------- Step 4: Vault / Storage ----------------
@router.post("/vault")
def vault_step(req: VaultRequest, session: Session = Depends(get_session)):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Vault confirmation required")

    wallet_id = str(uuid.uuid4())
    order = GoldOrder(user_id=req.user_id, step="VAULT_CONFIRM", wallet_id=wallet_id)
    session.add(order)
    session.commit()
    session.refresh(order)
    return {
        "message": "Vault storage confirmed ✅",
        "wallet_id": wallet_id,
        "next_endpoint": "/api/gold/receipt",
        "order_id": order.id,
    }


# ---------------- Step 5: Receipt ----------------
@router.post("/receipt")
def receipt_step(req: ReceiptRequest, session: Session = Depends(get_session)):
    orders = session.exec(
        f"SELECT * FROM goldorder WHERE user_id={req.user_id} ORDER BY id ASC"
    ).all()
    if not orders:
        raise HTTPException(status_code=400, detail="No orders found for user")

    kyc_order = next((o for o in orders if o.step == "KYC"), None)
    quantity_order = next((o for o in orders if o.step == "QUANTITY"), None)
    payment_order = next((o for o in orders if o.step == "PAYMENT"), None)
    vault_order = next((o for o in orders if o.step == "VAULT_CONFIRM"), None)

    receipt = {
        "user_id": req.user_id,
        "kyc_details": kyc_order.kyc_details if kyc_order else "",
        "quantity_grams": quantity_order.quantity_grams if quantity_order else 0,
        "amount": quantity_order.amount if quantity_order else 0,
        "payment_method": payment_order.payment_method if payment_order else "",
        "transaction_id": payment_order.transaction_id if payment_order else "",
        "wallet_id": vault_order.wallet_id if vault_order else "",
        "purchase_time": datetime.now(timezone.utc).isoformat(),
        "message": "Purchase complete 🎉",
    }

    # Save final POST_BUY step
    order = GoldOrder(user_id=req.user_id, step="POST_BUY")
    session.add(order)
    session.commit()
    session.refresh(order)

    return {"receipt": receipt, "order_id": order.id}
