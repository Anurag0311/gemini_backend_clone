from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Dict
from datetime import date

from response.format import response_format_error, response_format_success, response_format_success_fetching
from auth.auth_utils import get_current_user
from DB.connection import get_db
from DB.models import User, Chatroom, ChatroomHistory
from DB.schema import MessageSchema
from utils.utils import generate_batch_id
from redis_client import RedisDep
from celery.result import AsyncResult
from core.celery_worker import celery_app
from service.gemini_task import get_and_store

import traceback
import json

router = APIRouter()


@router.post("/chatroom")
async def create_chatroom(current_user: Dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:#TODO: remove redis cache for chatroom_id
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
    

@router.get("/chatroom")
async def get_chatrooms(redis_client: RedisDep, current_user: Dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        user_id = current_user.get('user_id', None)
        if user_id == None:
            return response_format_error(data= "Cannot find user")
        
        user_id = int(user_id)

        response = await redis_client.get(f"chatroom-{user_id}")
        if response:
           response = json.loads(response)
           return response_format_success_fetching(data=response)
        
        data = await db.execute(select(Chatroom.chatroom_id).where(Chatroom.user_id == user_id))
        data = data.scalars().all()

        dict_data = [{"chatroom_id": row} for row in data]

        await redis_client.setex(f"chatroom-{user_id}", 600, json.dumps(dict_data))

        return response_format_success_fetching(data=dict_data)
        
    except Exception as e:
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")


@router.get("/chatroom/{chatroom_id}")
async def get_chatrooms(chatroom_id : str,  current_user: Dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        user_id = current_user.get('user_id', None)
        if user_id == None:
            return response_format_error(data= "Cannot find user")
        
        user_id = int(user_id)

        chatroom = await db.execute(select(Chatroom).where(Chatroom.chatroom_id == chatroom_id))
        chatroom = chatroom.scalars().first()
        if not chatroom:
            return response_format_error(data="Chatroom not found")
        
        chats = await db.execute(select(ChatroomHistory).where(ChatroomHistory.chat_id == chatroom.id).order_by(desc(ChatroomHistory.created_at)))
        chats = chats.scalars().all()
        if not chats:
            return response_format_success_fetching(data="No chats")
        
        response = [{"prompt": chat.request_message, "prompt_response": chat.response_message} for chat in chats]
        return response_format_success_fetching(data=response)
    except Exception as e:
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")
    


@router.post("/chatroom/{chatroom_id}")
async def prompt(chatroom_id : str, request : MessageSchema, redis_client: RedisDep, current_user: Dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        user_id = current_user.get('user_id', None)
        if user_id == None:
            return response_format_error(data= "Cannot find user")
        
        user_id = int(user_id)

        user = await db.execute(select(User).where(User.id == int(user_id)))
        user = user.scalars().first()
        if not user:
            return response_format_error(data = "User Not Found")
        
        chatroom = await db.execute(select(Chatroom).where(Chatroom.chatroom_id == chatroom_id))
        chatroom = chatroom.scalars().first()
        if not chatroom:
            return response_format_error(data="Chatroom not found")
        
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

            if count >= 5:
                return response_format_error(data="Daily Limit Reached")


        task = get_and_store.delay(request.message, chatroom.id)

        return response_format_success(data = {
        "task_id": task.id,
        "status": "processing"
        })
    except Exception as e:
        traceback.print_exc()
        return response_format_error(data="Internal Server Error")
    

@router.get("/chatroom/message-status/{task_id}")
def check_message_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    print(result)
    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "done", "response": result.result}
    else:
        return {"status": result.state.lower(), "response": str(result.result)}
