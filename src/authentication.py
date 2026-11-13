from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from src.mongodb.general_config import users, database
#from email.message import EmailMessage
import secrets
import smtplib
from config import Settings
import os

settings = Settings()


def get_password_hash(password: str) -> str:    
    safe_password = password.encode("utf-8")[:72]
    hashed_bytes = bcrypt.hashpw(safe_password, bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe_password = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(safe_password,hashed_password.encode("utf-8"))

def create_access_token(data: dict) -> str:
    to_encode = data.copy() 
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm= ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate credential",
                                          headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    query = users.select().where(users.c.email == email)
    db_user = await database.fetch_one(query)

    if db_user is None:
        raise credentials_exception
    return db_user

