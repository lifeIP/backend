from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from app.auth import auth
from app.user import user_route
from app.image import image_route
from app.profile import profile_route
from app.project import project_route



app = FastAPI()


origins = [
    "http://localhost:3000",  # Только конкретно указанный домен
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"]  # Allows all headers
)

app.include_router(auth)
app.include_router(user_route)
app.include_router(image_route)
app.include_router(profile_route)
app.include_router(project_route)