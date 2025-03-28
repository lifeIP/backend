from fastapi import APIRouter, Request

from fastapi_auth_jwt import JWTAuthBackend, JWTAuthenticationMiddleware

from pydantic import BaseModel, Field
from typing import Optional



class User(BaseModel):
    username: str
    password: str
    token: Optional[str] = Field(None)


class AuthenticationSettings(BaseModel):
    secret: str = "secret-key"
    jwt_algorithm: str = "HS256"
    expiration_seconds: int = 3600 



class RegisterSchema(BaseModel):
    username: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str




auth = APIRouter()


auth_backend = JWTAuthBackend(
    authentication_config=AuthenticationSettings(),
    user_schema=User,
)


# Create Routes
@auth.post("/sign-up")
async def sign_up(request_data: RegisterSchema):
    return {"message": "User created"}


@auth.post("/login")
async def login(request_data: LoginSchema):
    token = await auth_backend.create_token(
        {
            "username": request_data.username,
            "password": request_data.password,
        }
    )
    return {"token": token}


@auth.get("/profile-info")
async def get_profile_info(request: Request):
    user: User = request.state.user
    return {"username": user.username}


@auth.post("/logout")
async def logout(request: Request):
    user: User = request.state.user
    await auth_backend.invalidate_token(user.token)
    return {"message": "Logged out"}
