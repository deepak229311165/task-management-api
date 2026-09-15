from datetime import datetime, timedelta, timezone
from database.connections import todos_table, database, users
from database.schemas import TodoCreate, TodoUpdate

async def save_otp(email: str, otp: str):
      expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
      query = users.update().where(users.c.email == email).values(
            otp = otp,
            otp_expires_at = expires_at
      )
      await database.execute(query)

async def verify_and_clear_otp(email: str,input_otp: str ) -> bool:
      query = users.select().where(users.c.email == email)
      user = await database.fetch_one(query)
      if not user or not user.otp or user.otp != input_otp:
            return False
      if user.otp_expires_at is None:
            return False
      now = datetime.now(timezone.utc)
      expiry = user.otp_expires_at
      if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo = timezone.utc)
      if now > expiry:
            return False
      
      update_query = users.update().where(users.c.email == email).values(
      otp = None,
      otp_expires_at = None,
      is_verified = True      
      )  
      await database.execute(update_query)
      return True

async def get_all_active_todos():
    query = todos_table.select().where(todos_table.c.is_active == True)
    rows = await database.fetch_all(query)
    return [dict(row) for row in rows]

async def insert_todo(new_task: TodoCreate) -> int:
    query = todos_table.insert().values(
        title=new_task.title,
        description=new_task.description,
        is_active=True,
        updated_at=datetime.utcnow()
    )
    return await database.execute(query)

async def get_todo_by_id(task_id: int,active_only: bool = True):
        if active_only:
            query = todos_table.select().where( 
                (todos_table.c.id == task_id) & (todos_table.c.is_active == True)
            )
        else:
            query = todos_table.select().where(todos_table.c.id == task_id)

        return await database.fetch_one(query)

async def update_todo_by_id(task_id: int, update_values: dict):
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
