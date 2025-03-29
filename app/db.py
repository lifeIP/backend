from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import (
    LargeBinary, 
    Column, 
    String, 
    Integer,
    Boolean, 
    UniqueConstraint, 
    PrimaryKeyConstraint
)
 
from fastapi import FastAPI


SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase): pass
 

class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True)
    
    first_name = Column(String(225), nullable=False) # Имя
    last_name = Column(String(225), nullable=False) # Фамилия
    patronymic = Column(String(225), nullable=True) # Отчество

    email = Column(String(225), nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False)



Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()