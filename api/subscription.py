from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv
from starlette.responses import JSONResponse

from typing import Dict
from DB.connection import get_db
from DB.models import User
from auth.auth_utils import get_current_user
from response.format import response_format_error, response_format_success, response_format_success_fetching

import stripe
import traceback
import os

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/subscribe/pro")
async def subscribe_pro(current_user: dict = Depends(get_current_user)):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": "price_1RmqCdB7az44GKPvVkpNywn0",  # Replace with your actual Stripe Price ID
                "quantity": 1,
            }],
            success_url="http://localhost:8000/stripe-success" + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/stripe-cancel",
            metadata={"user_id": current_user["user_id"]},
        )
        return {"checkout_url": session.url}
    except Exception as e:
        traceback.print_exc()
        # raise HTTPException(status_code=500, detail=str(e))
        return response_format_error(data="Error Occurred")
    

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]
    user_id = data["metadata"].get("user_id")

    if event_type == "checkout.session.completed":
        user_id = data["metadata"].get("user_id")
        if user_id:
            result = await db.execute(select(User).where(User.id == int(user_id)))
            user = result.scalar_one_or_none()
            if user:
                user.subscription_type = "Pro"
                await db.commit()
                return JSONResponse(status_code=200, content={"status": "user upgraded to pro"})
        return JSONResponse(status_code=400, content={"status": "user not found"})

    elif event_type == "invoice.payment_failed":
        return JSONResponse(status_code=200, content={"status": "user downgraded due to failure"})

    return JSONResponse(status_code=200, content={"status": f"event {event_type} handled"})


@router.get("/subscription/status")
async def subscription_status(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == int(current_user['user_id'])))
    user = result.scalar_one_or_none()
    return {"tier": "Pro" if user.subscription_type == "Pro" else "Basic"}
