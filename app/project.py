from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, PersonalData as _PersonalData, Classes as _Classes, Project as _Project
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
import os 
from fastapi_jwt_auth import AuthJWT
import random, string
from datetime import datetime

project_route = APIRouter()


def randompath(length: int):
    random_path = ''
    letters = string.ascii_lowercase
    for i in range(0, length):
       if i % 2 == 0: random_path += '/'
       random_path += random.choice(letters)
    return random_path


# TODO: Это заглушка
@project_route.get("/get_list_of_classes_in_project/{id}")
async def get_list_of_classes_in_project(id: int, db: Session = Depends(get_db)):
    return JSONResponse(content=jsonable_encoder([
        {
            "id": 0,
            "class_name": "eyes",
            "class_color": "#FF0000"
        },
        {
            "id": 1,
            "class_name": "lip",
            "class_color": "#0000FF"
        },
        {
            "id": 2,
            "class_name": "hair",
            "class_color": "#00FF00"
        },
    ]))




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
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")

    current_user=Authorize.get_jwt_identity()
    
    db_user = db.query(_User).filter(_User.id == current_user).first()
    db_project = _Project(name=project.name, description=project.description, users=db_user)
    
    for item in project.classes:
        db_classes = _Classes(label=item.label, description=item.description, color=item.color, projects=db_project)
        db.add(db_classes)
        db.commit()
        db.refresh(db_classes)
        
    db.flush(db_project)
    return JSONResponse(content=jsonable_encoder({"status": "Ok", "id":f"{db_project.id}" }))


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
    


    full_path = f"/images{randompath(8)}/"
    try:
        if not os.path.exists(os.getcwd() + full_path):
            os.makedirs(os.getcwd() + full_path)

    except Exception as e:
        print(e)
    
    current_dateTime = datetime.now()
    full_path = full_path + f"{current_dateTime.year}_{current_dateTime.month}_{current_dateTime.day}_{current_dateTime.hour}_{current_dateTime.minute}_{current_dateTime.second}." + file.filename.split(".")[-1]
    with open(os.getcwd() + full_path,'wb+') as f:
        f.write(file.file.read())
        f.close()
    
    db_project.photo_path = full_path

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return {"file_size": file.size}



# TODO: Это заглушка
@project_route.get("/get-image-by-id/{image_id}")
async def get_user_info_photo(image_id: int, db: Session = Depends(get_db)):
    db_personal_data = db.query(_PersonalData).filter(_PersonalData.user_id == 1).first()
    return FileResponse(os.getcwd() + db_personal_data.photo_path)