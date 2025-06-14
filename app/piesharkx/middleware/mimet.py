import sys, inspect, os, mimetypes
from typing import Union, Dict, List, Tuple, Any, Optional, Callable
from ..logger import logger

__all__ = ["BLOCK_SIZE"
    , "TYPE_LOADS", "mimetypes"
    , "MIMETypeHandler", "FileWrapper"]

BLOCK_SIZE = 1 << 16
# Enhanced mime types dictionary with more file types
TYPE_LOADS = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "css": "text/css",
    "js": "text/javascript",
    "html": "text/plain",
    "htm": "text/plain",
    "json": "application/json",
    "xml": "application/xml",
    "pdf": "application/pdf",
    "zip": "application/zip",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "wav": "audio/wav",
    "txt": "text/plain",
    "md": "text/markdown",
    "ico": "image/x-icon",
    # Additional common MIME types
    "woff": "font/woff",
    "woff2": "font/woff2",
    "ttf": "font/ttf",
    "otf": "font/otf",
    "eot": "application/vnd.ms-fontobject",
    "csv": "text/csv",
    "avi": "video/x-msvideo",
    "mkv": "video/x-matroska",
    "webm": "video/webm",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "yaml": "application/x-yaml",
    "yml": "application/x-yaml",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "rar": "application/vnd.rar",
    "7z": "application/x-7z-compressed",
    "tar": "application/x-tar",
    "gz": "application/gzip",
    "bz2": "application/x-bzip2",
}
try:
    mimetypes.init()
except:
    mimetypes._winreg = None
# Add or update mime types from our custom dictionary
for ext, mime_type in TYPE_LOADS.items():
    mimetypes.add_type(mime_type, f".{ext}")


class MIMETypeHandler:
    """Handler for MIME type detection and file operations"""

    @staticmethod
    def get_mime_type(file_path: str) -> tuple[str, str | None]:
        """
        Determine the MIME type of a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            A tuple of (MIME type, encoding type)
        """
        mime_type, encoding_type = mimetypes.guess_type(file_path)

        if mime_type is None:
            extension = os.path.splitext(file_path)[1].lower().lstrip(".")
            mime_type = TYPE_LOADS.get(extension, "application/octet-stream")
            logger.debug(f"Using fallback MIME type for {file_path}: {mime_type}")

        return mime_type, encoding_type

    @staticmethod
    def is_text_file(mime_type: str) -> bool:
        """
        Check if a file should be read as text based on its MIME type

        Args:
            mime_type: The MIME type to check

        Returns:
            True if the file should be read as text, False otherwise
        """
        text_mimes = [
            "text/",
            "application/json",
            "application/xml",
            "application/javascript",
            "application/x-yaml",
        ]
        return any(mime_type.startswith(prefix) for prefix in text_mimes)

    @staticmethod
    def read_file(file_path: str) -> Tuple[bytes, str]:
        """
        Read a file and determine its MIME type

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (file_content, mime_type)
        """
        mime_type = MIMETypeHandler.get_mime_type(file_path)

        try:
            # Read the file based on its type
            if MIMETypeHandler.is_text_file(mime_type):
                # Text files should be read as text
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().encode("utf-8")
            else:
                # Binary files should be read as binary
                with open(file_path, "rb") as f:
                    content = f.read()

            logger.debug(f"Successfully read file: {file_path} as {mime_type}")
            return content, mime_type

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

    @staticmethod
    def stream_file(file_path: str):
        """
        Generator to stream a file in chunks

        Args:
            file_path: Path to the file

        Yields:
            Chunks of the file
        """
        mime_type = MIMETypeHandler.get_mime_type(file_path)

        try:
            # Always read in binary mode for streaming, regardless of type
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(BLOCK_SIZE)
                    if not chunk:
                        break
                    yield chunk

        except Exception as e:
            logger.error(f"Error streaming file {file_path}: {str(e)}")
            raise


class FileWrapper:
    """Enhanced file wrapper for serving files efficiently"""

    def __init__(self, filelike, blksize=8192):
        self.filelike = filelike
        self.blksize = blksize
        if hasattr(filelike, "close"):
            self.close = filelike.close

    def __getitem__(self, key):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        raise IndexError

    def __iter__(self):
        return self

    def __next__(self):
        data = self.filelike.read(self.blksize)
        if not data:
            raise StopIteration
        return data