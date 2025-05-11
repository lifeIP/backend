from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import FileResponse, Response
from fastapi.encoders import jsonable_encoder
import os 
from fastapi_jwt_auth import AuthJWT
import random, string
from datetime import datetime
import json
from io import BytesIO


from app.service.minio import save_image_in_project, save_mask_in_project, get_image_by_path, get_mask_by_path

from app.service.db import get_db, \
    User as _User, \
    PersonalData as _PersonalData, \
    Mask as _Mask, \
    Classes as _Classes, \
    Project as _Project, \
    Image as _Image


project_route = APIRouter()


def randompath(length: int):
    random_path = ''
    letters = string.ascii_lowercase
    for i in range(0, length):
       if i % 2 == 0: random_path += '/'
       random_path += random.choice(letters)
    return random_path


# TODO: Это заглушка
@project_route.get("/get_list_of_classes_in_project/{project_id}")
async def get_list_of_classes_in_project(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    
    # проверка авторизации пользователя
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity()

    # проверка принадлежит ли проект пользователю
    db_project = db.query(_Project).filter(_Project.id == project_id).first()
    if db_project is None or db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    # получение классов проекта
    class_list = []
    db_classes = db.query(_Classes).filter(_Classes.project_id == project_id).all()
    
    for item in db_classes:
        class_list.append(
            {
                "id": item.id,
                "class_name": f"{item.label}",
                "class_color": f"{item.color}",
                "class_description": f"{item.description}",
            }
        )
    

    return JSONResponse(content=jsonable_encoder(class_list))




class ProjectClass(BaseModel):
    id: int
    label: str
    description: str
    color: str

class CreateProjectSchema(BaseModel):
    name:str
    description: str
    classes: List[ProjectClass]

# TODO: Это заглушка
@project_route.post("/create-project/")
async def create_project(project: CreateProjectSchema, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity()
    

    db_user = db.query(_User).filter(_User.id == current_user).first()
    db_project = _Project(name=project.name, description=project.description, users=db_user)
    
    # проверка на присутствие классов
    if len(project.classes) == 0:
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
    for item in project.classes:
        db_classes = _Classes(label=item.label, description=item.description, color=item.color, projects=db_project)
        db.add(db_classes)
        db.commit()
        db.refresh(db_classes)
        
    db.flush(db_project)
    return JSONResponse(content=jsonable_encoder({"status": "Ok", "id":f"{db_project.id}" }))



class UpdateProjectSchema(BaseModel):
    id:int
    name:str
    description: str
    classes: List[ProjectClass]

@project_route.put("/update-project-settings/")
async def update_project_settings(project: UpdateProjectSchema, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity()
    
    db_project = db.query(_Project).filter(_Project.user_id == current_user).filter(_Project.id == project.id).first()
    
    if len(project.name) > 0: db_project.name = project.name
    if len(project.description) > 0: db_project.description = project.description
    
    # if len(project.classes) == 0:
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    db.flush(db_project)
        
    for item in project.classes:
        db_classes_f = db.query(_Classes).filter(_Classes.label == item.label).first()
        if db_classes_f is not None:
            continue
        db_classes = _Classes(label=item.label, description=item.description, color=item.color, projects=db_project)
        db.add(db_classes)
        db.commit()
        db.refresh(db_classes)
        
    return JSONResponse(content=jsonable_encoder({"status": "Ok", "id":f"{db_project.id}" }))




# TODO: Это заглушка
@project_route.get("/get-projects-id/")
async def create_project(db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity()

    db_projects = db.query(_Project).filter(_Project.user_id == current_user).all()
    
    project_ids = []
    for item in db_projects:
        project_ids.append(item.id)
    
    return JSONResponse(content=jsonable_encoder({ "ids":project_ids }))




class ProjectInfo(BaseModel):
    id: int
    name: str
    description: str

@project_route.get("/get-projects-info-by-id/{project_id}")
async def get_projects_info_by_id(project_id: int, db: Session = Depends(get_db)):
    db_projects = db.query(_Project).filter(_Project.id == project_id).first()
    if db_projects is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    project_info = ProjectInfo(id=db_projects.id, name=db_projects.name, description=db_projects.description)
    return JSONResponse(content=jsonable_encoder(project_info))


@project_route.get("/get-projects-photo-preview-by-id/{project_id}")
async def get_projects_photo_preview_by_id(project_id: int, db: Session = Depends(get_db)):
    db_projects = db.query(_Project).filter(_Project.id == project_id).first()
    if db_projects is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    return Response(content=db_projects.photo_data, media_type="image/png")


@project_route.post("/change_project-preview-image/{project_id}")
async def change_project_preview_image(project_id:int, file: UploadFile, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")

    current_user=Authorize.get_jwt_identity() 

    db_project = db.query(_Project).filter(_Project.id == project_id).first()
    if db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    db_project.photo_data = file.file.read()
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return {"file_size": file.size}



@project_route.post("/upload_image_in_project/{project_id}")
async def upload_image_in_project(project_id:int, file: UploadFile, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity() 
    db_project = db.query(_Project).filter(_Project.id == project_id).first()
    if db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    print(type(file))
    result = await save_image_in_project(project_id=project_id, file=file.file, length=file.size)
    
    db_image = _Image(project_id=db_project.id, image_data_path=result._object_name)
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    

    return {"file_size": 0}



@project_route.get("/get_projects_images_list/{project_id}/{start_index}")
async def get_projects_images_list(project_id:int, start_index: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity() 
    db_project = db.query(_Project).filter(_Project.id == project_id).first()
    if db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    
    # Определяем начало и конец диапазона
    per_page = 50  # фиксированное количество изображений на страницу   
    offset = max((start_index - 1) * per_page - 1, 0)  # рассчитываем правильное смещение

    # Выборка нужных изображений прямо в базе данных
    db_images = db.query(_Image.id)\
                  .filter(_Image.project_id == project_id)\
                  .order_by(_Image.id.asc())\
                  .offset(offset)\
                  .limit(per_page)\
                  .all()

    # Формирование итогового списка идентификаторов
    image_list = [img.id for img in db_images]
    print(offset)
    print(image_list)

    return JSONResponse(content={"ids": image_list})



class PointClass(BaseModel):
    id: int
    x: float
    y: float

class FormClass(BaseModel):
    class_id: int
    mask_type: int # 0 - rect/ 1 - poligon
    points: List[PointClass]

class MaskClass(BaseModel):
    forms: List[FormClass]
    canvasWidth: int
    canvasHeight: int 



@project_route.post("/set_mask_on_image/{image_id}")
async def set_mask_on_image(image_id:int, mask: MaskClass, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity() 
    
    db_image = db.query(_Image).filter(_Image.id == image_id).first()
    db_project = db.query(_Project).filter(_Project.id == db_image.project_id).first()

    if db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")


    mask_file = str(mask.model_dump_json()).encode("utf-8")
    result = await save_mask_in_project(project_id=db_project.id, image_path=db_image.image_data_path, file=BytesIO(mask_file), length=len(mask_file))
    # result._object_name
    
    db_mask = db.query(_Mask).filter(_Mask.image_id == db_image.id).first()
    if db_mask is None:
        new_mask = _Mask(image_id=db_image.id, mask_data_path=result._object_name)
        db.add(new_mask)
        db.commit()
        db.refresh(new_mask)    
    else:
        db_mask.mask_data_path = result._object_name
        db.add(db_mask)
        db.commit()
        db.refresh(db_mask)




@project_route.get("/get_mask_on_image/{image_id}")
async def get_mask_on_image(image_id:int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity() 
    
    db_image = db.query(_Image).filter(_Image.id == image_id).first()
    db_project = db.query(_Project).filter(_Project.id == db_image.project_id).first()

    if db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")


    db_mask = db.query(_Mask).filter(_Mask.image_id == db_image.id).first()
    if db_mask is None: return MaskClass(forms=[], canvasWidth=400, canvasHeight=300)

    result = get_mask_by_path(db_project.id, db_mask.mask_data_path)
    res_mask = []
    async for value in result:
        res_mask.append(value)
    res_mask = b''.join(res_mask)

    forms = MaskClass.model_validate_json(res_mask.decode("utf-8"))
    return forms
    




# TODO: Это заглушка
@project_route.get("/get-image-by-id/{image_id}")
async def get_user_info_photo(image_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity() 
    
    db_image = db.query(_Image).filter(_Image.id == image_id).first()
    db_project = db.query(_Project).filter(_Project.id == db_image.project_id).first()
    if db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    return StreamingResponse(
        get_image_by_path(db_project.id, db_image.image_data_path),
        media_type='application/octet-stream'
    )
    



class MemberEmailModel(BaseModel):
    member_email: str

@project_route.post("/add_new_member_in_project/")
async def add_new_member_in_project(data:MemberEmailModel, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity()



    return JSONResponse(content=jsonable_encoder({ "status": 1 }))

    