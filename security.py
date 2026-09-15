from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from database.connections import users, database
from email.message import EmailMessage
import secrets
import smtplib
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg.set_content(f"your email code is:{otp} it will expire in 5 minutes")
    msg["subject"] = "email verification code"
    msg["from"] = SMTP_USERNAME
    msg["to"] = to_email

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

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

