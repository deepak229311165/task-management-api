from datetime import datetime, timedelta, timezone
from src.mongodb.general_config import todos_table, database, users
import sqlalchemy
from src.utils import make_naive_utc


async def get_due_unsent_reminders(now: datetime):
    now_naive = make_naive_utc(now)
    
    join = todos_table.join(users, todos_table.c.user_id == users.c.id)
    query = (
        sqlalchemy.select(todos_table, users.c.email)   
        .select_from(join)
        .where(
            (todos_table.c.due_date.is_not(None))
            & (todos_table.c.due_date <= now_naive)
            & (todos_table.c.reminder_sent == False)
            & (todos_table.c.is_active == True)
        )
    )
    return await database.fetch_all(query)

async def mark_reminder_sent(task_id: int):
    query = todos_table.update().where(todos_table.c.id == task_id).values(reminder_sent=True)
    await database.execute(query)
