from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image, PersonalData as _PersonalData
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

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