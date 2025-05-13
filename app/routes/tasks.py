from fastapi import (
    APIRouter,
    Depends, 
    HTTPException, 
    status,
    UploadFile,
)
from app.service.db import (
    get_db,
    Task as _Task,
    Project as _Project,
    User as _User,
    Image as _Image,
    Member as _Member
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

from app.service.minio import (
    save_image_in_project, 
    save_mask_in_project, 
    get_image_by_path, 
    get_mask_by_path
)


task_route = APIRouter()


class TaskClass(BaseModel):
    project_id: PositiveInt
    author_user_id: PositiveInt
    assignee_user_id: PositiveInt
    description: str = Field(max_length=500)
    

@task_route.post("/create-task/")
async def create_task(task: TaskClass, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)
    task.author_user_id = current_user
    # Проверяем проект на существование и права пользователя
    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.project_id == task.project_id)\
        .first()
    if db_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid project_id")
    
    # Проверяем получателя на существование
    db_user = db.query(_User)\
        .filter(_User.id == task.assignee_user_id)\
        .first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid assignee_user_id")
    
    new_task = _Task(**task.model_dump())

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.flush(new_task)

    return JSONResponse(content=jsonable_encoder({"task_id": new_task.id}))



@task_route.post("/upload_image_in_project/{project_id}")
async def upload_image_in_project(project_id:int, 
                                  file: UploadFile, 
                                  db: Session = Depends(get_db), 
                                  Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize) 
    
    # Проверяем проект на существование и права пользователя
    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.project_id == project_id)\
        .first()
    if db_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid project_id")

    db_task = db.query(_Task)\
        .filter(_Task.project_id == project_id)\
        .filter(_Task.status == False)\
        .first()
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid task")

    result = await save_image_in_project(project_id=project_id, file=file.file, length=file.size)
    db_image = _Image(project_id=project_id, image_data_path=result._object_name)    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    db_task.target_quantity = db_task.target_quantity + 1
    db.add(db_image)
    db_task.images.append(db_image)
    db.commit()
    db.refresh(db_task)

    return JSONResponse(content=jsonable_encoder({"file_size": file.size}))


