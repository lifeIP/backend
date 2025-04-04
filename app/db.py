from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy import (
    LargeBinary, 
    Column, 
    String, 
    Integer,
    ForeignKey,
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
    
    first_name = Column(String(255), nullable=False) # Имя
    last_name = Column(String(255), nullable=False) # Фамилия
    patronymic = Column(String(255), nullable=True) # Отчество

    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False)

    images = relationship("Image", back_populates="user")
    projects = relationship("Project", back_populates="user")



class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    full_path = Column(String(255), nullable=False, unique=True)
    user_id = Column(ForeignKey("users.id")) 
    user = relationship("User", back_populates="images")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(ForeignKey("users.id"))
    user = relationship("User", back_populates="projects")


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()