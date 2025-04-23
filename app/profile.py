from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image, PersonalData as _PersonalData
from fastapi.responses import FileResponse, Response
from datetime import datetime
import os
import base64
import random, string
from io import BytesIO


profile_route = APIRouter()



def randompath(length: int):
    random_path = ''
    letters = string.ascii_lowercase
    for i in range(0, length):
       if i % 2 == 0: random_path += '/'
       random_path += random.choice(letters)
    return random_path


@profile_route.post("/upload-image-on-profile/")
async def create_file(file: UploadFile, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")

    current_user=Authorize.get_jwt_identity() 

    
    db_user = db.query(_PersonalData).filter(_PersonalData.user_id == current_user).first()
    db_user.photo_data = file.file.read()

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"file_size": file.size}


@profile_route.get("/get-image-on-profile/{user_id}")
async def get_user_info_photo(user_id: int, db: Session = Depends(get_db)):
    db_personal_data = db.query(_PersonalData).filter(_PersonalData.user_id == user_id).first()
    if db_personal_data.id is None:
        return FileResponse(os.getcwd() + "/images/noimage.jpg")
    return Response(content=db_personal_data.photo_data, media_type="image/png")
