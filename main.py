from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from exceptions.handlers import validation_exception_handler

import uvicorn

from api import users, chatroom, subscription

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

app.include_router(users.router, prefix="/api/v1/user")
app.include_router(chatroom.router, prefix="/api/v1/chatroom")
app.include_router(subscription.router, prefix="/api/v1/subscription")


app.add_exception_handler(RequestValidationError, validation_exception_handler)
#TODO: ADD HTTPEXCEPTION HANDLER


# app start from here
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True, workers=6)