from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from typing import Dict
from DB.connection import get_db
from DB.models import User
from DB.schema import SignUpSchema, OTPSchema, VerifyOTPSchema, VerifyOTPPasswordSchema, ChangePasswordSchema
from auth.auth_utils import get_password_hash, create_access_token, get_current_user
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


@router.post("/auth/forgot-password")
@router.post("/auth/send-otp")
async def send_otp(request: OTPSchema, redis_client: RedisDep, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.mobile == request.mobile))
        result = result.scalars().first()
        if not result:
            return response_format_error(data="Phone Number Not Found")
        
        otp = random.randint(100000, 999999)

        await redis_client.set(f"otp:{otp}", f"{result.id}", ex=120)
    
        return response_format_success_fetching(data={"OTP":f"{otp} (Valid for 120 seconds)"})
    except Exception as e:
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")
    

@router.post("/auth/verify-otp")
async def verify_otp(request: VerifyOTPSchema, redis_client: RedisDep, db: AsyncSession = Depends(get_db)):
    try:
        id = await redis_client.get(f"otp:{request.otp}")
        if not id:
            return response_format_error(data="OTP not valid")
        
        data = {'user_id':id}
        access_token = create_access_token(data = data)

        response = {
            "access_token": access_token
        }
        return response_format_success_fetching(data=response)
    except Exception as e:
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")
    

@router.post("/auth/reset-password")
async def reset_password(request:VerifyOTPPasswordSchema, redis_client: RedisDep, db: AsyncSession = Depends(get_db)):
    try:
        #TODO: TEST THIS
        id = await redis_client.get(f"otp:{request.otp}")
        if not id:
            return response_format_error(data="OTP not valid")
        
        user = await db.execute(select(User).where(User.id == id))
        user = user.scalars().first()
        if not user:
            return response_format_error(data = "User Not Found")
        
        password = get_password_hash(request.password)

        user.password_hash = password
        await db.commit()

        return response_format_success(data="SuccessFully Updated Password")
    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")


@router.post("/auth/change-password")
async def change_password(request: ChangePasswordSchema, current_user: Dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        #TODO: TEST THIS
        user_id = current_user.get('user_id', None)
        if user_id == None:
            return response_format_error(data= "Cannot find user")
        
        user = await db.execute(select(User).where(User.id == int(user_id)))
        user = user.scalars().first()
        if not user:
            return response_format_error(data = "User Not Found")
        
        password = get_password_hash(request.new_password)

        user.password_hash = password
        await db.commit()

        return response_format_success(data="SuccessFully Updated Password")
    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")


@router.get("/user/me")
async def user_info(current_user: Dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        #TODO: ADD NUMBER OF CONVERSATION
        user_id = current_user.get('user_id', None)
        if user_id == None:
            return response_format_error(data= "Cannot find user")
        
        user = await db.execute(select(User).where(User.id == int(user_id)))
        user = user.scalars().first()
        if not user:
            return response_format_error(data = "User Not Found")
        
        response = {
            "name": user.name,
            "email": user.email,
            "mobile_number": user.mobile
        }

        return response_format_success_fetching(data=response)

    except Exception as e:
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")
