from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class TodoList(BaseModel):
    tasks: list[TodoCreate]

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr 
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str 

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class TodoAICreate(BaseModel):
    text: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None    

class TodoSummaryResponse(BaseModel):
    summary: str