from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignUpSchema(BaseModel):
    mobile: str = Field(example="9876543210", min_length=10, max_length=10)
    name: Optional[str] = Field(None, example="Anurag Singh")
    email: Optional[EmailStr] = Field(None, example="anurag@example.com")
    password: Optional[str] = Field(None, example="securePassword123", min_length=6)

class OTPSchema(BaseModel):
    mobile: str = Field(min_length=10, max_length=10)