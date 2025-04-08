from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import auth
from app.user import user_route
from app.image import image_route
from app.profile import profile_route

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"]  # Allows all headers
)


app.include_router(auth)
app.include_router(user_route)
app.include_router(image_route)
app.include_router(profile_route)