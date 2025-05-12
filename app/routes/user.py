from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.service.db import get_db, User as _User, Image as _Image, PersonalData as _PersonalData
import os
from pydantic import ValidationError

from fastapi.responses import FileResponse
from pathlib import Path

from app.service.service import (
    auth
)


user_route = APIRouter()



@user_route.get('/user_info')
async def get_user_info(Authorize:AuthJWT=Depends(), db: Session = Depends(get_db)):
    current_user = auth(Authorize=Authorize)
    
    db_user = db.query(_User).filter(_User.id == current_user).first()
    db_personal_data = db.query(_PersonalData).filter(_PersonalData.user_id == current_user).first()

    
    return {
        "first_name": db_personal_data.first_name,
        "last_name": db_personal_data.last_name,
        "patronymic": db_personal_data.patronymic,
        "email": db_user.email,
        "is_admin": db_user.is_admin,
        }




