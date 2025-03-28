from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_auth_jwt import JWTAuthenticationMiddleware

from app.auth import auth, auth_backend



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"]  # Allows all headers
)


app.add_middleware(
    JWTAuthenticationMiddleware,
    backend=auth_backend,
    exclude_urls=["/sign-up", "/login"],
)


app.include_router(auth)