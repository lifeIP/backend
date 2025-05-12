from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from app.routes.auth import auth
from app.routes.user import user_route
from app.routes.profile import profile_route
from app.routes.project import project_route
from app.routes.tasks import task_route



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
app.include_router(profile_route)
app.include_router(project_route)
app.include_router(task_route)