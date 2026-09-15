import logging
from fastapi import FastAPI
from database.connections import database, create_tables
from routers.todo import router as todo_router
from routers.auth import router as auth_router

# 1. Configure the logging format and level
logging.basicConfig(
    level=logging.INFO, # Change to DEBUG for more verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# 2. Create a logger instance for this file
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("Application is starting up...")
    try:
        logger.info("Creating database tables...")
        create_tables() 
        
        logger.info("Connecting to the database...")
        await database.connect()
        logger.info("Database connection established successfully.")
        
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
        logger.info("Database disconnected successfully.")
    except Exception as e:
        logger.error(f"Error during database disconnect: {e}", exc_info=True)


app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(todo_router, prefix="/todos", tags=["todos"])
