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
    assignee_user_id: int
    description: str = Field(max_length=500)
    target_quantity: PositiveInt
    
    

@task_route.post("/create-task/")
async def create_task(task: TaskClass, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)
    task.author_user_id = current_user

    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.project_id == task.project_id)\
        .first()
    if db_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid project_id")
    
    if task.assignee_user_id == 0: 
        task.assignee_user_id = db_member.id
        
    # Проверяем получателя на существование
    db_user = db.query(_Member)\
        .filter(_Member.id == task.assignee_user_id)\
        .first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid assignee_user_id")
    
    new_task = _Task(**task.model_dump())

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.flush(new_task)

    return JSONResponse(content=jsonable_encoder({"task_id": new_task.id}))


@task_route.get("/get-member-task-info-in-project/{project_id}/{member_id}")
async def get_member_task_ids_in_project(project_id: int, member_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.project_id == project_id)\
        .first()
    if db_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid project_id or member_id")
    
    db_tasks = db.query(_Task)\
        .filter(_Task.assignee_user_id == member_id)\
        .filter(_Task.project_id == project_id)\
        .all()
    if db_tasks is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid project_id or member_id")
    
    task_info_list = []
    for task in db_tasks:
        task_info_list.append({"task_id": task.id, "description": task.description, "quantity": task.quantity})
    return JSONResponse(content=jsonable_encoder({"tasks": task_info_list}))


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

    db_task.quantity = db_task.quantity + 1
    if db_task.quantity >= db_task.target_quantity:
        db_task.status = True

    db.add(db_image)
    db_task.images.append(db_image)
    db.commit()
    db.refresh(db_task)

    return JSONResponse(content=jsonable_encoder({"file_size": file.size}))


@task_route.get("/upload_image_in_project_status/{project_id}")
async def upload_image_in_project_status(project_id:int, 
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
        .filter(_Task.author_user_id == current_user)\
        .filter(_Task.status == False)\
        .first()
    
    if db_task is None:
        return JSONResponse(content=jsonable_encoder({"status": 0}))
    return JSONResponse(content=jsonable_encoder({"status": 1}))
    