import logging
from fastapi import FastAPI
from database.connections import database, create_tables
import database.queries as db_queries
from routers.todo import router as todo_router
from routers.auth import router as auth_router
from routers.email import send_reminder_email
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timezone, datetime

# 1. Configure the logging format and level
logging.basicConfig(
    level=logging.INFO, # Change to DEBUG for more verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# 2. Create a logger instance for this file
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

app = FastAPI()

async def check_and_send_reminders():
    due = await db_queries.get_due_unsent_reminders(datetime.now(timezone.utc))
    for todo in due:
        try:
            await send_reminder_email(todo["email"], todo["title"], todo["description"])
            await db_queries.mark_reminder_sent(todo["id"])
        except Exception as e:
            logger.error(f" failed to send reminder for todo{todo['id']}: {e}")

@app.on_event("startup")
async def startup():
    logger.info("Application is starting up...")
    try:
        logger.info("Creating database tables...")
        create_tables() 
        
        logger.info("Connecting to the database...")
        await database.connect()
        logger.info("Database connection established successfully.")
        scheduler.add_job(check_and_send_reminders, "interval", minutes=1)
        scheduler.start()
    except Exception as e:
        # exc_info=True prints the full stack trace for easier debugging
        logger.error(f"Critical error during startup: {e}", exc_info=True)
        # Re-raise the exception so the app doesn't start in a broken state
        raise e

@app.on_event("shutdown")
async def shutdown():
    logger.info("Application is shutting down...")
    try:
        await database.disconnect()
        scheduler.shutdown()
        logger.info("Database disconnected successfully.")
    except Exception as e:
        logger.error(f"Error during database disconnect: {e}", exc_info=True)


app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(todo_router, prefix="/todos", tags=["todos"])
