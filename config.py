from dotenv import load_dotenv
import os
load_dotenv()

class Settings():

    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    SMTP_HOST=os.getenv ("SMTP_HOST")
    SMTP_PORT=int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME=os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD=os.getenv("SMTP_PASSWORD")

    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
    LLM_MODEL=os.getenv("LLM_MODEL")

    DATABASE_URL =os.getenv("DATABASE_URL")



