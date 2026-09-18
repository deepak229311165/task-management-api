from datetime import datetime, timedelta, timezone
from database.connections import todos_table, database, users
from database.schemas import TodoCreate, TodoUpdate
import sqlalchemy

# Helper function to convert any datetime/string input to a naive UTC datetime
def make_naive_utc(dt: datetime | str | None) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


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


async def get_all_active_todos():
    query = todos_table.select().where(todos_table.c.is_active == True)
    rows = await database.fetch_all(query)
    return [dict(row) for row in rows]


async def insert_todo(new_task: TodoCreate, user_id: int) -> int:
    # Ensure due_date is converted to a naive UTC datetime object
    due_date = make_naive_utc(new_task.due_date)

    query = todos_table.insert().values(
        user_id=user_id,
        title=new_task.title,
        description=new_task.description,
        due_date=due_date,
        reminder_sent=False,
        is_active=True,
        updated_at=datetime.utcnow()
    )
    return await database.execute(query)


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


async def get_todo_by_id(task_id: int, active_only: bool = True):
    if active_only:
        query = todos_table.select().where( 
            (todos_table.c.id == task_id) & (todos_table.c.is_active == True)
        )
    else:
        query = todos_table.select().where(todos_table.c.id == task_id)

    return await database.fetch_one(query)


async def update_todo_by_id(task_id: int, update_values: dict):
    if "due_date" in update_values:
        update_values["due_date"] = make_naive_utc(update_values["due_date"])

    update_values["updated_at"] = datetime.utcnow()
    query = todos_table.update().where(
        todos_table.c.id == task_id
    ).values(**update_values)
    
    await database.execute(query)


async def mark_todo_deleted(task_id: int):
    query = todos_table.update().where(
        todos_table.c.id == task_id
    ).values(is_active=False, updated_at=datetime.utcnow())
    await database.execute(query)