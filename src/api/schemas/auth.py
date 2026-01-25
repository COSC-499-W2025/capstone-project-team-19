from pydantic import BaseModel, Field, field_validator
from ..auth.security import validate_password_strength

class RegisterIn(BaseModel):
    username: str = Field(..., min_length=1, description="Username cannot be empty")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long and include upper/lowercase and a number")
    
    @field_validator('username')
    @classmethod
    def validate_username_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Username cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        return validate_password_strength(v)

class LoginIn(BaseModel):
    username: str = Field(..., min_length=1, description="Username cannot be empty")
    password: str = Field(..., min_length=1, description="Password cannot be empty")
    
    @field_validator('username')
    @classmethod
    def validate_username_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Username cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError('Password cannot be empty')
        return v

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"