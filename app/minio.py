import os
from minio import Minio
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
    return f"{random_name}.jpg"

def create_directory_if_not_exists(directory):
    """Создаёт директорию, если она ещё не существует"""
    if not os.path.exists(directory):
        os.makedirs(directory)

async def save_image_in_project(project_id: int, file):
    create_directory_if_not_exists("./dataset/")
    temp_file_path = "dataset/" + generate_random_filename()
    bucket_name = "project-" + str(project_id)

    async with aiofiles.open(temp_file_path, mode='wb') as tmp:
        await tmp.write(file)

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    
    result = client.fput_object(bucket_name, temp_file_path, temp_file_path)
    
    os.remove(temp_file_path)
    return result