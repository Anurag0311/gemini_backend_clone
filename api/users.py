from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from DB.connection import get_db
from DB.models import User
from DB.schema import SignUpSchema, OTPSchema
from auth.auth_utils import get_password_hash
from response.format import response_format_success, response_format_error, response_format_success_fetching

import traceback
import random
import os

from redis_client import RedisDep

router = APIRouter()


@router.post("/auth/signup")
async def sign_up(request: SignUpSchema, db: AsyncSession = Depends(get_db)):
    try:
        password = get_password_hash(request.password) if request.password else None

        # Check if email exists
        if request.email:
            result = await db.execute(select(User).where(User.email == request.email))
            if result.scalars().first():
                return response_format_error(data="Email Already Present")
        
        # Check if mobile exists
        result = await db.execute(select(User).where(User.mobile == request.mobile))
        if result.scalars().first():
            return response_format_error(data="Phone Number Already Present")
        
        # Create new user
        new_user = User(
            mobile=request.mobile,
            name=request.name,
            email=request.email,
            password_hash=password
        )
        db.add(new_user)
        await db.commit()
        return response_format_success(data="Successfully Added")

    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")


@router.post("/auth/send-otp")
async def send_otp(request: OTPSchema, redis_client: RedisDep, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.mobile == request.mobile))
        result = result.scalars().first()
        if not result:
            return response_format_error(data="Phone Number Not Found")
        
        otp = random.randint(100000, 999999)

        await redis_client.set(f"otp:{otp}", f"{result.id}", ex=60000)
    
        return response_format_success_fetching(data={"OTP":f"{otp} (Valid for 120 seconds)"})
    except Exception as e:
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")
