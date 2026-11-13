from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from src.schema import TodoCreate, TodoUpdate
from src.mongodb.general_config import todos_table, database, users
from src.utils import make_naive_utc


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

 