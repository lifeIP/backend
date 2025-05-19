import os
from typing import BinaryIO
from miniopy_async import Minio
import aiofiles
from tempfile import NamedTemporaryFile
from pathlib import Path
from string import ascii_letters, digits
from random import choice


# Настройки MinIO
MINIO_ENDPOINT = 'localhost:9000'
ACCESS_KEY = 'minioadmin'
SECRET_KEY = 'minioadmin'

client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False  # Используйте True, если ваше соединение защищено HTTPS
)

def generate_random_filename(length=10):
    """Генерируем случайное имя файла"""
    characters = ascii_letters + digits
    random_name = ''.join(choice(characters) for _ in range(length))
    return random_name


async def save_image_in_project(project_id: int, file: BinaryIO, length: int):
    temp_file_path = f"dataset/images/{generate_random_filename()}.jpg"
    bucket_name = "project-" + str(project_id)
    if not await client.bucket_exists(bucket_name):
        await client.make_bucket(bucket_name)

    result = await client.put_object(bucket_name=bucket_name, object_name=temp_file_path, data=file, length=length)    
    return result

async def save_mask_in_project(project_id: int, image_path:str, file: BinaryIO, length: int):
    temp_file_path = f"dataset/masks/{image_path.split('/')[-1].split('.')[0]}.msk"
    bucket_name = "project-" + str(project_id)
    if not await client.bucket_exists(bucket_name):
        await client.make_bucket(bucket_name)

    result = await client.put_object(bucket_name=bucket_name, object_name=temp_file_path, data=file, length=length)    
    return result




async def get_image_by_path(project_id:int, path:str):
    bucket_name = "project-" + str(project_id)
    response = await client.get_object(bucket_name, path)
    return await response.read()
    

async def get_mask_by_path(project_id:int, path:str):
    bucket_name = "project-" + str(project_id)
    response = await client.get_object(bucket_name, path)
    return await response.read()
