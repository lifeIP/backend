from sqlalchemy import create_engine
from typing import List
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy import (
    LargeBinary, 
    Column, 
    String, 
    Integer,
    ForeignKey,
    Boolean, 
    UniqueConstraint,
    Table
)
from sqlalchemy.orm import Mapped
 


SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False)

    projects = relationship("Project", back_populates="users")
    personal_data = relationship("PersonalData", back_populates="users")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_user_id")
    authored_tasks = relationship("Task", back_populates="author", foreign_keys="Task.author_user_id")


# Личные данные пользователя
class PersonalData(Base):
    __tablename__ = "personal_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id"), unique=True)
    first_name = Column(String(255), nullable=False)  # Имя
    last_name = Column(String(255), nullable=False)  # Фамилия
    patronymic = Column(String(255), nullable=True)  # Отчество
    photo_data = Column(LargeBinary, nullable=True)

    users = relationship("User", back_populates="personal_data")


# Проект
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
    tasks = relationship("Task", back_populates="project")


# Классы объектов в рамках проекта
class Classes(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"))

    label = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    color = Column(String(255), nullable=False)

    projects = relationship("Project", back_populates="classes")


# Изображения проекта
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"))
    image_data_path = Column(String(60), nullable=True)

    projects = relationship("Project", back_populates="images")
    masks = relationship("Mask", back_populates="image")
    tasks = relationship("Task", secondary="task_images", back_populates="images")


# Маски изображений
class Mask(Base):
    __tablename__ = "mask"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(ForeignKey("images.id"), unique=True)
    mask_data_path = Column(String(60), nullable=True)

    image = relationship("Image", back_populates="masks")


# Ассоциативная таблица для связи задач и изображений
task_images_association_table = Table(
    "task_images",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id")),
    Column("image_id", ForeignKey("images.id")),
    UniqueConstraint("task_id", "image_id"),
)


# Задача
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"), nullable=False)
    author_user_id = Column(ForeignKey("users.id"), nullable=False)
    assignee_user_id = Column(ForeignKey("users.id"), nullable=False)
    description = Column(String(500), nullable=False)
    status = Column(Boolean, nullable=False, default=False)

    project = relationship("Project", back_populates="tasks")
    author = relationship("User", back_populates="authored_tasks", foreign_keys=[author_user_id])
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_user_id])
    images: Mapped[List["Image"]] = relationship(
        "Image", secondary=task_images_association_table, back_populates="tasks"
    )


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()