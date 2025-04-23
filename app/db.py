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
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False)

    projects = relationship("Project", back_populates="users")
    personal_data = relationship("PersonalData", back_populates="users")

class PersonalData(Base):
    __tablename__ = "personal_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id"), unique=True)
    first_name = Column(String(255), nullable=False) # Имя
    last_name = Column(String(255), nullable=False) # Фамилия
    patronymic = Column(String(255), nullable=True) # Отчество
    photo_data = Column(LargeBinary, nullable=True)

    users = relationship("User", back_populates="personal_data")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id"))

    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    photo_data = Column(LargeBinary, nullable=True)

    users = relationship("User", back_populates="projects")
    images = relationship("Image", back_populates="projects")
    classes = relationship("Classes", back_populates="projects")


class Classes(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"))

    label = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    color = Column(String(255), nullable=False)

    projects = relationship("Project", back_populates="classes")

    
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"))
    image_data = Column(LargeBinary, nullable=True)
    
    projects = relationship("Project", back_populates="images")
    mask = relationship("Mask", back_populates="images")


class Mask(Base):
    __tablename__ = "mask"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(ForeignKey("images.id"), unique=True)
    mask_data = Column(LargeBinary, nullable=True)

    images = relationship("Image", back_populates="mask")


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()