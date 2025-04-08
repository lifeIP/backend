from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image, PersonalData as _PersonalData
import os

from fastapi.responses import FileResponse
from pathlib import Path

user_route = APIRouter()


@user_route.get('/user_info')
async def get_user_info(Authorize:AuthJWT=Depends(), db: Session = Depends(get_db)):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")


    current_user=Authorize.get_jwt_identity()
    
    db_user = db.query(_User).filter(_User.id == current_user).first()
    db_personal_data = db.query(_PersonalData).filter(_PersonalData.user_id == current_user).first()

    
    return {
        "first_name": db_personal_data.first_name,
        "last_name": db_personal_data.last_name,
        "patronymic": db_personal_data.patronymic,
        "email": db_user.email,
        "is_admin": db_user.is_admin,
        }




