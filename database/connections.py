import sqlalchemy
from sqlalchemy import table, column, String, Integer 
from datetime import datetime, UTC
from databases import Database
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

todos_table = sqlalchemy.Table(
    "todos",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, default=datetime.now(UTC),)
)

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String(50), unique=True, nullable=False, index=True),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("otp", sqlalchemy.String),
    sqlalchemy.Column("otp_expires_at", sqlalchemy.DateTime(timezone=True)),
    sqlalchemy.Column("is_verified", sqlalchemy.Boolean, default=False, nullable=False)

)   

def create_tables():
    sync_url = DATABASE_URL.replace("+asyncpg", "")
    sync_engine = sqlalchemy.create_engine(sync_url)
    metadata.create_all(sync_engine)
    sync_engine.dispose()


