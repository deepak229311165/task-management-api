import sqlalchemy
from config import Settings
from datetime import datetime, UTC
from databases import Database

settings = Settings()

database = Database(settings.DATABASE_URL)
metadata = sqlalchemy.MetaData()

todos_table = sqlalchemy.Table(
    "todos",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False),
    sqlalchemy.Column("title", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("due_date", sqlalchemy.DateTime, nullable=True),
    sqlalchemy.Column("reminder_sent", sqlalchemy.Boolean, default=False, nullable=False),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, default=lambda: datetime.now(UTC))
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
    sync_url = database.replace("+asyncpg", "")
    sync_engine = sqlalchemy.create_engine(sync_url)
    metadata.create_all(sync_engine)
    sync_engine.dispose()
