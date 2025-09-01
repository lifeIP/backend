from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import FileResponse, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
import os 
from fastapi_jwt_auth import AuthJWT
import random, string
from datetime import datetime
import json
from io import BytesIO

from app.service.service import (
    auth, 
    isTheProjectOwnedByTheUser,
    getProjectById,
    getImageById,
    getRightsIndexByProjectIdAndUserId,
    giveHimAccess
)


from app.service.minio import (
    remove_mask,
    save_image_in_project, 
    save_mask_in_project, 
    get_image_by_path, 
    get_mask_by_path
)

from app.service.db import (
    get_db,
    User as _User, 
    PersonalData as _PersonalData, 
    Mask as _Mask, 
    Classes as _Classes, 
    Project as _Project, 
    Image as _Image,
    Member as _Member,
    Invitation as _Invitation
)

project_route = APIRouter()


def randompath(length: int):
    random_path = ''
    letters = string.ascii_lowercase
    for i in range(0, length):
       if i % 2 == 0: random_path += '/'
       random_path += random.choice(letters)
    return random_path


@project_route.get("/get_list_of_classes_in_project/{project_id}")
async def get_list_of_classes_in_project(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    '''
    Возвращает список классов в проекте. Доступ <= 3.
    '''

    # проверка авторизации пользователя
    current_user = auth(Authorize=Authorize)

    isTheProjectOwnedByTheUser(db, current_user, project_id)
    giveHimAccess(db, project_id, current_user, 3)
    

    # получение классов проекта
    class_list = []
    db_classes = db.query(_Classes).filter(_Classes.project_id == project_id).all()
    
    for item in db_classes:
        class_list.append(
            {
                "id": item.id,
                "class_name": f"{item.label}",
                "class_color": f"{item.color}",
                "class_description": f"{item.description}",
            }
        )    

    return JSONResponse(content=jsonable_encoder(class_list))




class ProjectClass(BaseModel):
    id: int
    label: str
    description: str
    color: str

class CreateProjectSchema(BaseModel):
    name:str
    description: str
    classes: List[ProjectClass]

# TODO: Это заглушка
@project_route.post("/create-project/")
async def create_project(project: CreateProjectSchema, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    current_user = auth(Authorize=Authorize)
        

    try:
        # 3. Начинаем транзакцию
        with db.begin():
            # 4. Создаем новый проект
            new_project = _Project(name=project.name, description=project.description)
            db.add(new_project)
            db.flush()  # Предварительная фиксация состояния проекта для дальнейшего использования его ID

            # 5. Создаем первого участника проекта (текущего пользователя)
            new_member = _Member(user_id=current_user, project_id=new_project.id, user_rights=0, is_creator=True)
            db.add(new_member)

            # 6. Создаем классы для проекта
            for item in project.classes:
                if len(item.label) == 0: continue
                db_classes = _Classes(label=item.label, description=item.description, color=item.color, project_id=new_project.id)
                db.add(db_classes)
            
            # 7. Сохраняем изменения
            db.commit()

    except IntegrityError as ex:
        # Если произошла ошибка целостности (например, дубликат уникальных полей)
        #print(f"Database integrity error during project creation: {ex}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database integrity error occurred.")

    except Exception as ex:
        # Любая другая непредвиденная ошибка
        #print(f"Unexpected error creating project: {ex}")
        db.rollback()
        raise HTTPException(status_code=500, detail="An unexpected server error has occurred.")

    # 8. Возвращаем успешный ответ
    return JSONResponse(content=jsonable_encoder({"status": "OK", "id": new_project.id}))



class UpdateProjectSchema(BaseModel):
    id:int
    name:str
    description: str
    classes: List[ProjectClass]

@project_route.put("/update-project-settings/")
async def update_project_settings(project: UpdateProjectSchema, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    current_user = auth(Authorize=Authorize)
    
    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.project_id == project.id)\
        .first()
    if db_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")    

    db_project = db.query(_Project)\
        .filter(_Project.id == db_member.project_id)\
        .first()
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")    

    if len(project.name) > 0: db_project.name = project.name # type: ignore
    if len(project.description) > 0: db_project.description = project.description # type: ignore
    
    # if len(project.classes) == 0:
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    db.flush(db_project) # type: ignore
        
    for item in project.classes:
        if len(item.label) == 0: continue
        
        db_classes_f = db.query(_Classes)\
            .filter(_Classes.project_id == db_member.project_id)\
            .filter(_Classes.label == item.label)\
            .first()
        
        if db_classes_f is not None:
            continue
        db_classes = _Classes(label=item.label, description=item.description, color=item.color, projects=db_project)
        db.add(db_classes)
        db.commit()
        db.refresh(db_classes)
        
    return JSONResponse(content=jsonable_encoder({"status": "Ok", "id":f"{db_project.id}" }))




# TODO: Это заглушка
@project_route.get("/get-projects-ids/")
async def get_projects_ids(db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    current_user = auth(Authorize=Authorize)

    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.is_creator == True)\
        .all()
    
    project_ids = []
    for item in db_member:
        project_ids.append(item.project_id)
    
    return JSONResponse(content=jsonable_encoder({ "ids":project_ids }))


@project_route.get("/get-outside-projects-ids/")
async def get_outside_projects_ids(db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    current_user = auth(Authorize=Authorize)

    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.is_creator == False)\
        .all()
    
    project_ids = []
    for item in db_member:
        project_ids.append(item.project_id)
    
    return JSONResponse(content=jsonable_encoder({ "ids":project_ids }))


class ProjectInfo(BaseModel):
    id: int
    name: str
    description: str
    user_rights: int

@project_route.get("/get-projects-info-by-id/{project_id}")
async def get_projects_info_by_id(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    # проверка принадлежит ли проект пользователю
    db_member = isTheProjectOwnedByTheUser(db, current_user, project_id)

    db_projects = getProjectById(db, project_id)
    
    project_info = ProjectInfo(
        id=db_projects.id,  # type: ignore
        name=db_projects.name,  # type: ignore
        description=db_projects.description,  # type: ignore
        user_rights=db_member.user_rights # type: ignore
        )
    return JSONResponse(content=jsonable_encoder(project_info))


@project_route.get("/get-projects-photo-preview-by-id/{project_id}")
async def get_projects_photo_preview_by_id(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    db_projects = getProjectById(db, project_id)
    
    return Response(content=db_projects.photo_data, media_type="image/png")


@project_route.post("/change_project-preview-image/{project_id}")
async def change_project_preview_image(project_id:int, file: UploadFile, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    # проверка принадлежит ли проект пользователю
    db_member = isTheProjectOwnedByTheUser(db, current_user, project_id)
    
    db_project = getProjectById(db, project_id)
    
    db_project.photo_data = file.file.read() # type: ignore
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return {"file_size": file.size}


@project_route.get("/get_projects_images_list/{project_id}/{start_index}")
async def get_projects_images_list(project_id:int, start_index: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize) 
    
    # проверка принадлежит ли проект пользователю
    db_member = isTheProjectOwnedByTheUser(db, current_user, project_id)
    
    
    # Определяем начало и конец диапазона
    per_page = 50  # фиксированное количество изображений на страницу   
    offset = max((start_index - 1) * per_page - 1, 0)  # рассчитываем правильное смещение

    # Выборка нужных изображений прямо в базе данных
    db_images = db.query(_Image.id)\
                  .filter(_Image.project_id == project_id)\
                  .order_by(_Image.id.asc())\
                  .offset(offset)\
                  .limit(per_page)\
                  .all()

    # Формирование итогового списка идентификаторов
    image_list = [img.id for img in db_images]
    
    db_count = db.query(_Project.total_images_count)\
        .filter(_Project.id == project_id)\
        .first()
    if db_count is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    return JSONResponse(content={"ids": image_list, "total_images_count": db_count[0]})


@project_route.get("/get_projects_dataset_images_list/{project_id}/{start_index}")
async def get_projects_dataset_images_list(project_id:int, start_index: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize) 
    
    # проверка принадлежит ли проект пользователю
    db_member = isTheProjectOwnedByTheUser(db, current_user, project_id)
    
    
    # Определяем начало и конец диапазона
    per_page = 50  # фиксированное количество изображений на страницу   
    offset = max((start_index - 1) * per_page - 1, 0)  # рассчитываем правильное смещение

    # Выборка нужных изображений прямо в базе данных
    db_images = db.query(_Image.id)\
                  .filter(_Image.project_id == project_id)\
                  .filter(_Image.is_marked_up == True)\
                  .order_by(_Image.id.asc())\
                  .offset(offset)\
                  .limit(per_page)\
                  .all()

    # Формирование итогового списка идентификаторов
    image_list = [img.id for img in db_images]
    
    db_count = db.query(_Project.total_images_count)\
        .filter(_Project.id == project_id)\
        .first()
    if db_count is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")
    
    return JSONResponse(content={"ids": image_list, "total_images_count": db_count[0]})


@project_route.get("/get_image_purpose/{image_id}")
async def get_image_purpose(image_id:int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)
    db_image = getImageById(db, image_id)
    return JSONResponse(content={"purpose": db_image.image_purpose}) # type: ignore




class PointClass(BaseModel):
    id: int
    x: float
    y: float

class FormClass(BaseModel):
    class_id: int
    mask_type: int # 0 - rect/ 1 - poligon
    points: List[PointClass]
    canvasWidth: int
    canvasHeight: int 

class MaskClass(BaseModel):
    forms: List[FormClass]



@project_route.post("/set_mask_on_image/{image_id}")
async def set_mask_on_image(image_id:int, mask: MaskClass, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize) 
    
    if len(mask.forms) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid mask")
    

    db_image = getImageById(db, image_id)

    db_member = isTheProjectOwnedByTheUser(db, current_user, db_image.project_id) # type: ignore
    
    

    db_mask = db.query(_Mask).filter(_Mask.image_id == db_image.id).first()
    if db_mask is not None:
        result = await get_mask_by_path(db_member.project_id, db_mask.mask_data_path) # type: ignore
        result = result.decode("utf-8")
        await remove_mask(db_member.project_id, db_mask.mask_data_path) # type: ignore

        for item in mask.forms:
            db_class = db.query(_Classes)\
                .filter(_Classes.id == item.class_id)\
                .first()
            if(db_class.count >= 1): # type: ignore
                db_class.count -= 1 # type: ignore
            else:
                continue
            db.add(db_class)
        db.commit()

    mask_file = str(mask.model_dump_json()).encode("utf-8")
    result = await save_mask_in_project(
        project_id=db_member.project_id,  # type: ignore
        image_path=db_image.image_data_path,  # type: ignore
        file=BytesIO(mask_file), 
        length=len(mask_file))
    
    if db_mask is None:
        new_mask = _Mask(image_id=db_image.id, mask_data_path=result._object_name)
        db_image.is_marked_up = True # type: ignore

        for item in mask.forms:
            db_class = db.query(_Classes)\
                .filter(_Classes.id == item.class_id)\
                .first()
            #print(db_class.count)
            db_class.count += 1 # type: ignore
            db.add(db_class)

        db.add(db_image)
        db.add(new_mask)
        db.commit()
    else:
        db_mask.mask_data_path = result._object_name # type: ignore
        db_image.is_marked_up = True # type: ignore
        for item in mask.forms:
            
            db_class = db.query(_Classes)\
                .filter(_Classes.id == item.class_id)\
                .first()
            #print(db_class.count)
            db_class.count += 1 # type: ignore
            db.add(db_class)
        db.add(db_image)
        db.add(db_mask)
        db.commit()





@project_route.get("/get_mask_on_image/{image_id}")
async def get_mask_on_image(image_id:int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize) 
    
    db_image = db.query(_Image).filter(_Image.id == image_id).first()

    db_member = isTheProjectOwnedByTheUser(db, current_user, db_image.project_id) # type: ignore
    
    db_mask = db.query(_Mask).filter(_Mask.image_id == db_image.id).first() # type: ignore
    if db_mask is None: return MaskClass(forms=[])

    result = await get_mask_by_path(db_member.project_id, db_mask.mask_data_path) # type: ignore
    

    forms = MaskClass.model_validate_json(result.decode("utf-8"))
    return forms
    




# TODO: Это заглушка
@project_route.get("/get-image-by-id/{image_id}")
async def get_user_info_photo(image_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize) 
    
    db_image = getImageById(db, image_id)
    
    db_member = isTheProjectOwnedByTheUser(db, current_user, db_image.project_id) # type: ignore

    photo = await get_image_by_path(db_image.project_id, db_image.image_data_path) # type: ignore
    
    return Response(content=photo, media_type="image/png")

    



class MemberEmailModel(BaseModel):
    project_id: int
    member_email: str

@project_route.post("/add_new_member_in_project/")
async def add_new_member_in_project(data:MemberEmailModel, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)
    
    # проверка принадлежит ли проект пользователю
    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.project_id == data.project_id)\
        .filter(_Member.user_rights == 0)\
        .first()
    if db_member is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project_id or email")

    db_invitee = db.query(_User)\
        .filter(_User.email == data.member_email)\
        .filter(_User.id != current_user)\
        .first()
    if db_invitee is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project_id or email")

    db_invitation = db.query(_Invitation)\
        .filter(_Invitation.invitee_id == db_invitee.id)\
        .filter(_Invitation.inviter_id == current_user)\
        .filter(_Invitation.project_id == data.project_id)\
        .first()
    
    if db_invitation is None:
        new_invitation = _Invitation(project_id=data.project_id, inviter_id=current_user, invitee_id=db_invitee.id)
        db.add(new_invitation)
        db.commit()
    return JSONResponse(content=jsonable_encoder({ "status": 1 }))


@project_route.get("/get_all_members_in_project_without_me/{project_id}")
async def get_all_members_in_project_without_me(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)
    
    # проверка принадлежит ли проект пользователю
    db_member = isTheProjectOwnedByTheUser(db, current_user, project_id)

    db_member = db.query(_Member)\
        .filter(_Member.user_id != current_user)\
        .filter(_Member.project_id == project_id)\
        .all()
    
    members = []
    for item in db_member:
        db_data = db.query(_PersonalData).filter(_PersonalData.user_id == item.user_id).first()
        if db_data is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project_id or email")

        members.append({
            "name": db_data.last_name + " " + db_data.first_name,
            "member_id": item.id,
            "is_creator": item.is_creator,
            "user_rights": item.user_rights,
        })
    return JSONResponse(content=jsonable_encoder({ "members": members }))


@project_route.get("/get_all_members_in_project/{project_id}")
async def get_all_members_in_project(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)
    # проверка принадлежит ли проект пользователю
    db_member = isTheProjectOwnedByTheUser(db, current_user, project_id)


    db_member = db.query(_Member)\
        .filter(_Member.project_id == project_id)\
        .all()
    
    members = []
    for item in db_member:
        db_data = db.query(_PersonalData).filter(_PersonalData.user_id == item.user_id).first()
        if db_data is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project_id or email")

        members.append({
            "name": db_data.last_name + " " + db_data.first_name,
            "member_id": item.id,
            "is_creator": item.is_creator,
            "user_rights": item.user_rights,
        })
    return JSONResponse(content=jsonable_encoder({ "members": members }))



@project_route.get("/get_all_invitation/")
async def get_all_invitation(db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    # проверка принадлежит ли проект пользователю
    db_invitation = db.query(_Invitation)\
        .filter(_Invitation.invitee_id == current_user)\
        .limit(6)\
        .all()
    if db_invitation is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project_id or email")

    invitation = []
    for item in db_invitation:
        db_personal_data = db.query(_PersonalData)\
            .filter(_PersonalData.user_id == item.inviter_id)\
            .first()
        db_project = db.query(_Project)\
            .filter(_Project.id == item.project_id)\
            .first()
        invitation.append({
            "id": item.id, 
            "sender": db_personal_data.last_name + " " + db_personal_data.first_name, # type: ignore
            "project": db_project.name # type: ignore
            })
    return JSONResponse(content=jsonable_encoder({ "invitations": invitation }))

@project_route.get("/accept_invitation/{invitation_id}")
async def accept_invitation(invitation_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    db_invitation = db.query(_Invitation)\
        .filter(_Invitation.id == invitation_id)\
        .filter(_Invitation.invitee_id == current_user)\
        .first()
    if db_invitation is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid invitation_id")
    
    db_member = db.query(_Member)\
        .filter(_Member.user_id == current_user)\
        .filter(_Member.project_id == db_invitation.project_id)\
        .first()
    if db_member is None: 
        new_member = _Member(user_id=current_user, project_id=db_invitation.project_id, user_rights=db_invitation.role)
        db.add(new_member)
    
    db.delete(db_invitation)
    db.commit()

    return JSONResponse(content=jsonable_encoder({ "status": 1 }))

@project_route.get("/decline_invitation/{invitation_id}")
async def decline_invitation(invitation_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)

    db_invitation = db.query(_Invitation)\
        .filter(_Invitation.id == invitation_id)\
        .filter(_Invitation.invitee_id == current_user)\
        .first()
    if db_invitation is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid invitation_id")
    
    db.delete(db_invitation)
    db.commit()

    return JSONResponse(content=jsonable_encoder({ "status": 1 }))



@project_route.get("/get_series_for_pie/{project_id}")
async def get_series_for_pie(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    current_user = auth(Authorize=Authorize)
    isTheProjectOwnedByTheUser(db, current_user, project_id)
    giveHimAccess(db, project_id, current_user, 2)
    
    # получение классов проекта
    class_list = []
    db_classes = db\
        .query(_Classes)\
        .filter(_Classes.project_id == project_id)\
        .all()

    for item in db_classes:
        class_list.append(
            {   
                "class_id": f"{item.id}",
                "class_name": f"{item.label}",
                "class_color": f"{item.color}",
                "class_count": f"{item.count}",
                "class_photo_count": f"{item.count}",
                "class_description": f"{item.description}",
            }
        )    

    return JSONResponse(content=jsonable_encoder(class_list))



@project_route.get("/get_data_of_classes_for_rebalancing/{project_id}")
async def get_data_of_classes_for_rebalancing(project_id: int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    current_user = auth(Authorize=Authorize)

    # проверка принадлежит ли проект пользователю
    db_member = isTheProjectOwnedByTheUser(db, current_user, project_id)
    
    db_dataset = db\
        .query(_Project)\
        .filter(_Project.id == project_id)\
        .first()
    if db_dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid project id")

    return JSONResponse(content=jsonable_encoder({"image_count": db_dataset.dataset_images.__len__()}))



class DatasetFormClass(BaseModel):
    excludedClassListID: List[str]

@project_route.post("/generate_dataset/{project_id}")
async def generate_dataset(toDo: DatasetFormClass, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
    # проверка авторизации пользователя
    current_user = auth(Authorize=Authorize)

    print(current_user, toDo)
