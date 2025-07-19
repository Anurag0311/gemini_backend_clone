from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict
from datetime import date

from response.format import response_format_error, response_format_success, response_format_success_fetching
from auth.auth_utils import get_current_user
from DB.connection import get_db
from DB.models import User, Chatroom, ChatroomHistory
from utils.utils import generate_batch_id

import traceback

router = APIRouter()


@router.post("/chatroom")
async def create_chatroom(current_user: Dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        user_id = current_user.get('user_id', None)
        if user_id == None:
            return response_format_error(data= "Cannot find user")
        
        user_id = int(user_id)
        
        user = await db.execute(select(User).where(User.id == int(user_id)))
        user = user.scalars().first()
        if not user:
            return response_format_error(data = "User Not Found")

        if user.subscription_type == 'basic':
            stmt = (
                select(func.count(ChatroomHistory.id))
                .join(Chatroom, Chatroom.id == ChatroomHistory.chat_id)
                .where(
                    Chatroom.user_id == user_id,
                    func.date(ChatroomHistory.created_at) == date.today()
                )
            )
            result = await db.execute(stmt)
            count = result.scalar_one()

            if count <= 4:
                chatroom_id = generate_batch_id("chatroom")
                db.add(Chatroom(
                    user_id = user_id,
                    chatroom_id = chatroom_id
                ))

                await db.commit()
                return response_format_success_fetching(data={"chatroom_id": chatroom_id})
            else:
                return response_format_error(data="Daily prompt limit reached")
        else:
            #TODO: CHECK SUBSCRIPTION EXPIRATION_DATE Logic
            chatroom_id = generate_batch_id("chatroom")
            db.add(Chatroom(
                user_id = user_id,
                chatroom_id = chatroom_id
            ))

            await db.commit()
            return response_format_success_fetching(data={"chatroom_id": chatroom_id})

    except Exception as e:
        db.rollback()
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")