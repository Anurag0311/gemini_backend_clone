# exceptions/handlers.py
from fastapi import Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    loc = exc.errors()[0].get('loc')
    msg = exc.errors()[0].get('msg')
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Failed",
            "msg": loc[1]+ " " + msg
        },
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    if type(exc.detail) == str:
        message = exc.detail
    elif isinstance(exc.detail, dict):
        message = exc.detail.get("message")
    else:
        message = "An HTTP error occurred"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "message": message,
            "data": exc.detail.get("data") if isinstance(exc.detail, dict) else {},
        },
    )


