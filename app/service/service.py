from fastapi import HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session

from app.service.db import (
    get_db,
    User as _User, 
    PersonalData as _PersonalData, 
    Mask as _Mask, 
    Classes as _Classes, 
    Project as _Project, 
    Image as _Image,
    Member as _Member,
    Invitation as _Invitation
)


def auth(Authorize:AuthJWT):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user:int=Authorize.get_jwt_identity() # type: ignore
    return current_user

# проверка принадлежит ли проект пользователю
def isTheProjectOwnedByTheUser(db: Session, user_id: int, project_id: int):
    db_member = db\
        .query(_Member)\
        .filter(_Member.user_id == user_id)\
        .filter(_Member.project_id == project_id)\
        .first()
    if db_member is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    return db_member

def getProjectById(db: Session, project_id: int):
    db_projects =\
        db.query(_Project)\
        .filter(_Project.id == project_id)\
        .first()
    if db_projects is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    return db_projects

def getImageById(db: Session, image_id: int):
    db_image = db.query(_Image).filter(_Image.id == image_id).first()
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid image id")
    return db_image