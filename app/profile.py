from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image, PersonalData as _PersonalData
from fastapi.responses import FileResponse
from datetime import datetime
import os


profile_route = APIRouter()

@profile_route.post('/upload-image-on-profile/', status_code=200)
async def upload_image_on_profile(image: UploadFile = File(...), db: Session = Depends(get_db)):
    # try:
    #     Authorize.jwt_required()
    # except Exception as e:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")

    # current_user=Authorize.get_jwt_identity()

    current_dateTime = datetime.now()
    full_path = f"/images/{current_dateTime.year}/{current_dateTime.month}/{current_dateTime.day}/{current_dateTime.hour}/{current_dateTime.minute}/{current_dateTime.second}/"
    
    user_id = 1

    try:
        if not os.path.exists(os.getcwd() + full_path):
            os.makedirs(os.getcwd() + full_path)

    except Exception as e:
        print(e)
    
    full_path = full_path + f"{current_dateTime.microsecond}." + image.filename.split(".")[-1]
    with open(os.getcwd() + full_path,'wb+') as f:
        f.write(image.file.read())
        f.close()
    
    db_user = db.query(_PersonalData).filter(_PersonalData.user_id == user_id).first()
    db_user.photo_path = full_path

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return



@profile_route.get("/get-image-on-profile/{user_id}")
async def get_user_info_photo(user_id: int, db: Session = Depends(get_db)):
    db_personal_data = db.query(_PersonalData).filter(_PersonalData.user_id == user_id).first()
    return FileResponse(os.getcwd() + db_personal_data.photo_path)