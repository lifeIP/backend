from fastapi import APIRouter, Request, Depends, HTTPException, status

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional
from typing import Literal

from app.service.db import get_db, User as _User, PersonalData as _PersonalData
from functools import wraps


from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import datetime


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
        raise HTTPException(status_code=400)
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400)
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

class Settings(BaseSettings):
    authjwt_access_token_expires:datetime.timedelta=datetime.timedelta(hours=12)
    authjwt_secret_key:str='e8ae5c5d5cd7f0f1bec2303ad04a7c80f09f759d480a7a5faff5a6bbaa4078d0'

@AuthJWT.load_env # type: ignore
def get_settings():
    return Settings()


@auth.post("/sign-up", status_code=201)
async def sign_up(user: RegisterSchema, db: Session = Depends(get_db)):
     #TODO: Надо сделать валидацию
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=401, detail="User already registered") 

    hashed_password = get_password_hash(user.password)
    
    db_user = _User(email=user.email, hashed_password=hashed_password, is_admin=False)
    personal_data = _PersonalData(first_name=user.first_name, last_name=user.last_name, patronymic=user.patronymic, users=db_user)
    
    db.add(personal_data)
    db.commit()
    db.refresh(personal_data)
    return personal_data


@auth.post("/login")
async def login(request_data: LoginSchema, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    #TODO: Надо сделать валидацию
    db_user = get_user(db, email=request_data.email)
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Bad password or email")
    
    if not verify_password(request_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Bad password or email")
    
    access_token=Authorize.create_access_token(identity=db_user.id) # type: ignore
    refresh_token=Authorize.create_refresh_token(identity=db_user.id) # type: ignore

    return {"access_token":access_token,"refresh_token":refresh_token, "user_id": db_user.id}



@auth.get('/protected')
async def get_logged_in_user(Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize) # type: ignore
    return {"current_user":current_user}


