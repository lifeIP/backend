from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image
from fastapi.responses import FileResponse
from datetime import datetime
import os

image_route = APIRouter()



@image_route.post('/upload-image')
async def upload_image(image: UploadFile = File(...), Authorize:AuthJWT=Depends(), db: Session = Depends(get_db)):
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

    db_image = _Image(full_path=full_path, user_id=user_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    db_image = db.query(_Image).filter(_Image.full_path == full_path).first()
    return {
        "full_path": db_image.full_path,
        "imgage_id": db_image.id
        }


# @image_route.post('/image-by-path')
# async def get_image(full_path: str, Authorize:AuthJWT=Depends(), db: Session = Depends(get_db)):
#     try:
#         Authorize.jwt_required()
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")

#     current_user=Authorize.get_jwt_identity()

#     db.query(_Image).filter(_Image.user_id == current_user).filter(_Image.full_path == full_path).first()
#     return FileResponse()
