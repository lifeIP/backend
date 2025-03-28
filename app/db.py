from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import  Column, Integer, String
 
from fastapi import FastAPI


SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

class Base(DeclarativeBase): pass
 

class User(Base):
    __tablename__ = "people"
 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)

 
Base.metadata.create_all(bind=engine)