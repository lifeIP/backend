from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db import get_db, User as _User, Image as _Image

user_route = APIRouter()


@user_route.get('/user_info')
async def get_user_info(Authorize:AuthJWT=Depends(), db: Session = Depends(get_db)):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")


    current_user=Authorize.get_jwt_identity()

    db_user = db.query(_User).filter(_User.id == current_user).first()
    
    return {
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "patronymic": db_user.patronymic,
        "email": db_user.email,
        "is_admin": db_user.is_admin,
        }
