import aiosmtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_PASS = os.getenv("SMTP_PASSWORD")

async def send_reminder_email (to_email: str, title: str, description: str | None):
    msg = EmailMessage()
    msg["From"]= SMTP_USER
    msg["To"]= to_email
    msg["Subject"]= f"reminder: {title}"
    msg.set_content(f"{title}\n\n{description or ''}")

    await aiosmtplib.send(
        msg,
        hostname= SMTP_HOST,
        port= SMTP_PORT,
        username= SMTP_USER,
        password= SMTP_PASS,
        use_tls=True,
    )
     

