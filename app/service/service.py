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



def getRightsIndexByProjectIdAndUserId(db: Session, project_id: int, user_id: int):
    '''Возвращает права пользователя: 0 - наивисший уровень. 4 - пользователь без прав'''
    db_member = isTheProjectOwnedByTheUser(db, user_id, project_id)
    if(db_member.is_creator): # type: ignore
        return 0
    else:
        return int(db_member.user_rights) # type: ignore
    

def giveHimAccess(db: Session, project_id: int = -1, user_id: int = -1, right_index: int = 4):
    '''Вызывает ошибку если у пользователя недостаточно прав'''
    if(project_id == -1 or project_id == -1):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")

    print("RIGHT: ", right_index, " / ", getRightsIndexByProjectIdAndUserId(db, project_id, user_id))
    if(right_index < getRightsIndexByProjectIdAndUserId(db, project_id, user_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    


# возвращает проект по id
def getProjectById(db: Session, project_id: int):
    db_projects =\
        db.query(_Project)\
        .filter(_Project.id == project_id)\
        .first()
    if db_projects is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    return db_projects


# возвращает изображение по id
def getImageById(db: Session, image_id: int):
    db_image = db.query(_Image).filter(_Image.id == image_id).first()
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid image id")
    return db_image