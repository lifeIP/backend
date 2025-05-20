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
    Table,
    DateTime
)
from sqlalchemy.orm import Mapped
from datetime import datetime
from sqlalchemy.sql import func
 


SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

dataset_images_association_table = Table(
    "dataset_images",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id")),
    Column("image_id", ForeignKey("images.id")),
    Column("image_purpose", Integer),  # Целочисленное поле назначения (0-test, 1-train, 2-valid)
    UniqueConstraint("project_id", "image_id"),
)

task_images_association_table = Table(
    "task_images",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id")),
    Column("image_id", ForeignKey("images.id")),
    UniqueConstraint("task_id", "image_id"),
)

# Пользователь
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False)

    # Many-to-many relation with Projects through Member table
    members = relationship("Member", back_populates="user")

    # Other relations
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


# Инвайты
class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Integer, nullable=False, default=2)  # 0 - admin, 1 - observer, 2 - worker
    status = Column(Integer, nullable=False, default=0)  # 0 - open, 1 - accepted, 2 - declined
    sent_at = Column(DateTime(timezone=True), server_default=func.now())


# Проект
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    photo_data = Column(LargeBinary, nullable=True)
    total_images_count = Column(Integer, default=0)

    # Dataset images (используем ассоциативную таблицу)
    dataset_images: Mapped[List["Image"]] = relationship(
        "Image", secondary=dataset_images_association_table, back_populates="projects"
    )

    # Members of this project
    members = relationship("Member", back_populates="projects")

    # Other relationships
    classes = relationship("Classes", back_populates="projects")
    tasks = relationship("Task", back_populates="projects")


# Участник проекта
class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    is_creator = Column(Boolean, default=False)
    user_rights = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Обратные связи
    user = relationship("User", back_populates="members")
    projects = relationship("Project", back_populates="members")


# Классы объектов в рамках проекта
class Classes(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"))

    label = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    color = Column(String(255), nullable=False)

    projects = relationship("Project", back_populates="classes")


# Изображение
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"))
    image_data_path = Column(String(60), nullable=True)

    projects = relationship("Project", secondary="dataset_images", back_populates="dataset_images")
    masks = relationship("Mask", back_populates="image")
    tasks = relationship("Task", secondary="task_images", back_populates="images")


# Маска изображения
class Mask(Base):
    __tablename__ = "mask"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(ForeignKey("images.id"), unique=True)
    mask_data_path = Column(String(60), nullable=True)

    image = relationship("Image", back_populates="masks")


# Задача
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("projects.id"), nullable=False)
    author_user_id = Column(ForeignKey("users.id"), nullable=False)
    assignee_user_id = Column(ForeignKey("users.id"), nullable=False)
    description = Column(String(500), nullable=False)
    status = Column(Boolean, nullable=False, default=False)

    quantity = Column(Integer, default=0)
    target_quantity = Column(Integer, default=0)

    projects = relationship("Project", back_populates="tasks")
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