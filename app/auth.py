from fastapi import APIRouter, Request, Depends, HTTPException, status

from pydantic import BaseModel, Field
from typing import Optional

from app.db import get_db, User as _User
from functools import wraps


from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from passlib.context import CryptContext



# Хэширование пароля+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
# Хэширование пароля-----------------------------------------------------------


# Работа с базой данных++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def get_user(db: Session, email: str):
    return db.query(_User).filter(_User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
# Работа с базой данных--------------------------------------------------------






class RegisterSchema(BaseModel):
    email:str
    password: str
    first_name: str
    last_name: str
    patronymic: str
    


class LoginSchema(BaseModel):
    email: str
    password: str




auth = APIRouter()

class Settings(BaseModel):
    authjwt_secret_key:str='e8ae5c5d5cd7f0f1bec2303ad04a7c80f09f759d480a7a5faff5a6bbaa4078d0'

@AuthJWT.load_env
def get_config():
    return Settings()


@auth.post("/sign-up", status_code=201)
async def sign_up(user: RegisterSchema, db: Session = Depends(get_db)):
     #TODO: Надо сделать валидацию
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=401, detail="User already registered")

    hashed_password = get_password_hash(user.password)
    db_user = _User(first_name=user.first_name, last_name=user.last_name, patronymic=user.patronymic, email=user.email, hashed_password=hashed_password, is_admin=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@auth.post("/login")
async def login(request_data: LoginSchema, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    #TODO: Надо сделать валидацию
    db_user = get_user(db, email=request_data.email)
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Bad password or email")
    
    if not verify_password(request_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Bad password or email")
    
    access_token=Authorize.create_access_token(identity=db_user.id)
    refresh_token=Authorize.create_refresh_token(identity=db_user.id)

    return {"access_token":access_token,"refresh_token":refresh_token}



@auth.get('/protected')
async def get_logged_in_user(Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")


    current_user=Authorize.get_jwt_identity()

    return {"current_user":current_user}


