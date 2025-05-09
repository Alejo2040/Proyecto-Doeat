from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    CASHIER = "cashier"

class UserBase(BaseModel):
    """Esquema base para usuarios"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: Optional[UserRole] = UserRole.CASHIER
    
class UserCreate(UserBase):
    """Esquema para crear usuarios"""
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class UserLogin(BaseModel):
    """Esquema para inicio de sesión"""
    username: str
    password: str

class UserResponse(UserBase):
    """Esquema para respuestas con datos de usuario"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    """Esquema para actualizar usuarios"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class TokenData(BaseModel):
    """Esquema para datos incluidos en tokens"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None

