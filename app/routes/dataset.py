from fastapi import (
    APIRouter,
    Depends, 
    HTTPException, 
    status,
    UploadFile,
)
from app.service.db import (
    get_db,
    Task as _Task,
    Project as _Project,
    User as _User,
    Image as _Image,
    Member as _Member
)
from app.service.service import (
    auth
)

from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from pydantic import (
    BaseModel, 
    Field, 
    PositiveInt
)

from app.service.minio import (
    save_image_in_project, 
    save_mask_in_project, 
    get_image_by_path, 
    get_mask_by_path
)

from app.service.service import (
    auth
)

dataset_route = APIRouter()



    

# @dataset_route.post("/move_task_images_in_dataset/{project_id}/{task_id}", status_code=201)
# async def move_task_images_in_dataset(project_id:int, task_id:int, db: Session = Depends(get_db), Authorize:AuthJWT=Depends()):
#     current_user = auth(Authorize=Authorize)

