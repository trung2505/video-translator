import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional
from fastapi import UploadFile
from app.core.config import get_settings

settings = get_settings()


class StorageInterface(ABC):
    @abstractmethod
    def save_uploaded_file(self, upload_file: UploadFile) -> str:
        pass

    @abstractmethod
    def save_processed_file(self, src_path: str, dest_filename: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def get_local_path(self, stored_path: str) -> str:
        pass


class LocalStorage(StorageInterface):
    def __init__(self, media_root: Optional[str] = None):
        self.media_root = media_root or settings.MEDIA_ROOT
        os.makedirs(self.media_root, exist_ok=True)
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

    def save_uploaded_file(self, upload_file: UploadFile) -> str:
        filename = upload_file.filename
        out_path = os.path.join(self.media_root, filename)
        with open(out_path, "wb") as dest:
            shutil.copyfileobj(upload_file.file, dest)
        return out_path

    def save_processed_file(self, src_path: str, dest_filename: Optional[str] = None) -> str:
        if not dest_filename:
            dest_filename = os.path.basename(src_path)
        dest_path = os.path.join(settings.PROCESSED_DIR, dest_filename)
        shutil.copy2(src_path, dest_path)
        return dest_path

    def get_local_path(self, stored_path: str) -> str:
        # For local storage, stored_path is already a filesystem path or URL.
        return stored_path
