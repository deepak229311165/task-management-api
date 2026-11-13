from datetime import datetime, timedelta, timezone
from src.mongodb.general_config import todos_table, database, users
from src.utils import make_naive_utc
import secrets
from email.message import EmailMessage
import smtplib
from config import Settings

def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"

async def save_otp(email: str, otp: str):
    expires_at = make_naive_utc(datetime.now(timezone.utc) + timedelta(minutes=5))
    query = users.update().where(users.c.email == email).values(
        otp=otp,
        otp_expires_at=expires_at
    )
    await database.execute(query)

async def verify_and_clear_otp(email: str, input_otp: str) -> bool:
    query = users.select().where(users.c.email == email)
    user = await database.fetch_one(query)
    if not user or not user.otp or user.otp != input_otp:
        return False
    if user.otp_expires_at is None:
        return False
        
    now = datetime.utcnow()
    expiry = user.otp_expires_at
    if expiry.tzinfo is not None:
        expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
        
    if now > expiry:
        return False
      
    update_query = users.update().where(users.c.email == email).values(
        otp=None,
        otp_expires_at=None,
        is_verified=True      
    )   
    await database.execute(update_query)
    return True

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg.set_content(f"your email code is:{otp} it will expire in 5 minutes")
    msg["subject"] = "email verification code"   
    msg["from"] = Settings.SMTP_USERNAME
    msg["to"] = to_email

    with smtplib.SMTP_SSL(Settings.SMTP_HOST, Settings.SMTP_PORT) as server:
        server.login(Settings.SMTP_USERNAME, Settings.SMTP_PASSWORD)
        server.send_message(msg)
