from fastapi import HTTPException, Depends, APIRouter
#from src.todo import 
from src.schema import TodoAICreate, TodoCreate, TodoList, TodoUpdate, TodoSummaryResponse
import src.todo as db_queries
from src.authentication import get_current_user
import llm.service as llm_service # needs to be changed


router = APIRouter(dependencies=Depends(get_current_user))

@router.get("/")
async def get_all_todos():
    return await db_queries.get_all_active_todos()

@router.get("/summary", response_model=TodoSummaryResponse)
async def summarize_todos():
    todos = await db_queries.get_all_active_todos()
    summary_text = await llm_service.summarize_todos(todos)
    return TodoSummaryResponse(summary=summary_text)

@router.post("/")
async def create_task(new_task: TodoCreate, current_user = Depends(get_current_user)):
    try:
        record_id = await db_queries.insert_todo(new_task, user_id = current_user.id)
        return{"status_code":200, "id": record_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"some error occurred: {e}")

@router.post("/ai")
async def create_task_from_text(payload: TodoAICreate, current_user = Depends(get_current_user)):
    try:
        parsed_task = await llm_service.parse_natural_language_todo(payload.text)

        created_tasks = []
        for task in parsed_task: 
            record_id = await db_queries.insert_todo(task, user_id = current_user.id)
            created_tasks.append({
                "id": record_id,
                "title": task.title,
                "description": task.description,
                "due_date": task.due_date
        })
        return created_tasks
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"some error occurred: {e}")

@router.put("/{task_id}")
async def update_task(task_id: int, updated_task: TodoUpdate):
    try:
        existing_doc = await db_queries.get_todo_by_id(task_id, active_only =True)
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Task not found")

        update_values = updated_task.model_dump(exclude_unset=True)
        if not update_values:
            raise HTTPException(status_code=400, detail="no field provided to update")
        await db_queries.update_todo_by_id(task_id, update_values)
        return {"status code": 200, "message": "Task updated successfully"}
    except HTTPException:
        raise   
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"some error occurred: {e}")

@router.delete("/{task_id}")
async def delete_task(task_id: int):
    try:
        existing_doc = await db_queries.get_todo_by_id(task_id, active_only=True)
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Task not found")
        await db_queries.mark_todo_deleted(task_id)
        return {"Status code": 200, "message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"some error occurred: {e}")


