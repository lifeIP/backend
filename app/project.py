from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, PersonalData as _PersonalData, Mask as _Mask, Classes as _Classes, Project as _Project, Image as _Image
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, Response
from fastapi.encoders import jsonable_encoder
import os 
from fastapi_jwt_auth import AuthJWT
import random, string
from datetime import datetime
import json


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
    
    db_image = _Image(project_id=db_project.id, image_data=file.file.read())
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return {"file_size": file.size}



@project_route.get("/get_projects_images_list/{project_id}")
async def get_projects_images_list(project_id:int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity() 
    db_project = db.query(_Project).filter(_Project.id == project_id).first()
    if db_project.user_id != current_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    
    db_images = db.query(_Image).filter(_Image.project_id == project_id).all()
    image_list = []
    for item in db_images:
        image_list.append(item.id)

    return JSONResponse(content=jsonable_encoder({ "ids": image_list }))



class PointClass(BaseModel):
    id: int
    x: float
    y: float

class FormClass(BaseModel):
    class_id: int
    points: List[PointClass]

class MaskClass(BaseModel):
    forms: List[FormClass]


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


    db_mask = db.query(_Mask).filter(_Mask.image_id == db_image.id).first()
    
    
    
    if db_mask.id is None:
        new_mask = _Mask(image_id=db_image.id, mask_data=json.dumps(mask, indent=4, default=str).encode("utf-8"))
        db.add(new_mask)
        db.commit()
        db.refresh(new_mask)
        print(new_mask.mask_data)
    else:
        db_mask.mask_data = json.dumps(mask, indent=4, default=str).encode("utf-8")
        db.add(db_mask)
        db.commit()
        db.refresh(db_mask)

        print(db_mask.mask_data)



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
    
    return Response(content=db_image.image_data, media_type="image/png")
