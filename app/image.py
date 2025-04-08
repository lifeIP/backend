from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image, PersonalData as _PersonalData
from fastapi.responses import FileResponse
from datetime import datetime
import os
import shutil

image_route = APIRouter()


# @image_route.post("/upload_photo/")
# async def upload_photo(file: UploadFile = File(...)):
#     # Сохраняем временный файл на сервере
#     with open(f"./uploads/{file.filename}", "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
    
#     return {"filename": file.filename}


