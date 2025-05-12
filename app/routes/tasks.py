from fastapi import (
    APIRouter,
    Depends, 
)
from app.service.db import (
    get_db,
    Task as _Task,
)
from app.service.service import (
    auth
)

from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session


from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from pydantic import (
    BaseModel, 
    Field, 
    PositiveInt
)


task_route = APIRouter()


class TaskClass(BaseModel):
    project_id: PositiveInt
    author_user_id: PositiveInt
    assignee_user_id: PositiveInt
    description: str = Field(max_length=500)
    

@task_route.get("/create-task/")
async def create_task(task: TaskClass, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    new_task = _Task(**task.model_dump())


    # db_task = db.query(_Task).filter().first()
    return JSONResponse(content=jsonable_encoder({}))
