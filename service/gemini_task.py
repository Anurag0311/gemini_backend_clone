from core.celery_worker import celery_app
from utils.utils import get_gemini_response
from DB.connection_sync import get_sync_db
from DB.models import ChatroomHistory

import traceback

@celery_app.task
def get_and_store(prompt: str, chat_id:int):
    try:
        response = get_gemini_response(prompt)
        conn = next(get_sync_db())

        conn.add(ChatroomHistory(
            chat_id = chat_id,
            request_message = prompt,
            response_message = response
        ))
        conn.commit()

        return response
    except Exception as e:
        print(f"[TASK] Exception: {e}")
        traceback.print_exc()  # <-- this prints the full traceback
        return f"[Gemini error] {str(e)}"