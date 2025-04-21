from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image, PersonalData as _PersonalData
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
import os 

project_route = APIRouter()



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
    

@project_route.post("/create-project/")
async def create_project(project: CreateProjectSchema):
    print(project)
    return JSONResponse(content=jsonable_encoder({"status": "Ok"}))



# TODO: Это заглушка
@project_route.get("/get-image-by-id/{image_id}")
async def get_user_info_photo(image_id: int, db: Session = Depends(get_db)):
    db_personal_data = db.query(_PersonalData).filter(_PersonalData.user_id == 1).first()
    return FileResponse(os.getcwd() + db_personal_data.photo_path)