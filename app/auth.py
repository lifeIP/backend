from fastapi import APIRouter, Request, Depends, HTTPException, status

from fastapi_auth_jwt import JWTAuthBackend, JWTAuthenticationMiddleware

from pydantic import BaseModel, Field
from typing import Optional

from app.db import engine, SessionLocal, Base, get_db, User as _User
from functools import wraps



from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, email: str):
    return db.query(_User).filter(_User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user




class AuthBase(BaseModel):
    token: Optional[str] = Field(None)

class User(AuthBase):
    email: str
    username: str
    password: str


class AuthenticationSettings(BaseModel):
    secret: str = "secret-key"
    jwt_algorithm: str = "HS256"
    expiration_seconds: int = 3600 



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


auth_backend = JWTAuthBackend(
    authentication_config=AuthenticationSettings(),
    user_schema=User,
)





# Create Routes
@auth.post("/sign-up")
async def sign_up(user: RegisterSchema, db: Session = Depends(get_db)):
    #TODO: Надо сделать валидацию
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = _User(first_name=user.first_name, last_name=user.last_name, patronymic=user.patronymic, email=user.email, hashed_password=hashed_password, is_admin=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user




@auth.post("/login")
async def login(request_data: LoginSchema, db: Session = Depends(get_db)):
    #TODO: Надо сделать валидацию
    db_user = get_user(db, email=request_data.email)
    
    if not db_user:
        raise HTTPException(status_code=400, detail="Bad password or email")
    
    if not verify_password(request_data.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Bad password or email")
    
    token = await auth_backend.create_token(
        {
            "id": db_user.id,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "patronymic": db_user.patronymic
        }
    )
    return {"token": token}



@auth.post("/logout")
async def logout(request: AuthBase):
    await auth_backend.invalidate_token(request.token)
    return {"message": "Logged out"}
