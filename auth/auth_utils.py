from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.exceptions import HTTPException

from DB.connection import get_db
from DB.models import User
from response.format import response_format_error

import jwt
import os


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = str(os.getenv("SECRET_KEY", 'secret_key'))
ALGORITHM = str(os.getenv("ALGORITHM", "HS256"))
ACCESS_TOKEN_EXPIRE_MINUTES = 1440


def verify_password(plain_password, hashed_password):
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to check against.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Generate a hashed password from a plain text password.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create an access token encoded with the provided data and expiration time.

    Args:
        data (dict): The payload data to include in the token.
        expires_delta (timedelta, optional): The time duration for which the token is valid.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
)-> dict:
    """Retrieve the current user based on the token."""

    token = token.replace("Bearer ", "").strip()


    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.execute(select(User).where(User.id == int(payload['user_id'])))
    user = user.scalars().first()
    if not user:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response_format_error(data="User not found")
            )

    return payload


def verify_token(token: str):
    """
    Verify and decode a JWT token.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Optional[dict]: The decoded payload if the token is valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
