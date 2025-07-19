from celery import Celery
from utils.utils import get_gemini_response
from dotenv import load_dotenv

import os

load_dotenv()

celery_app = Celery(
    "gemini_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")  # allows getting result
)

import service.gemini_task
    