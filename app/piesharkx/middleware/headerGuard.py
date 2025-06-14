import os, sys, json, hashlib
from datetime import datetime, timedelta
from .mimet import mimetypes
from ..logger import logger

__all__ = ["Middleware"
    , "CORSMiddleware", "SecurityHeadersMiddleware"
    , "EnhancedStaticHandler"]

class Middleware:
    """Base middleware class"""

    def process_request(self, request):
        return request

    def process_response(self, response):
        return response


class CORSMiddleware(Middleware):
    """Cross-Origin Resource Sharing middleware"""

    def __init__(
        self, allowed_origins=None, allowed_methods=None, allowed_headers=None
    ):
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
        ]
        self.allowed_headers = allowed_headers or ["Content-Type", "Authorization"]

    def process_response(self, response):
        response.headers["Access-Control-Allow-Origin"] = ", ".join(
            self.allowed_origins
        )
        response.headers["Access-Control-Allow-Methods"] = ", ".join(
            self.allowed_methods
        )
        response.headers["Access-Control-Allow-Headers"] = ", ".join(
            self.allowed_headers
        )
        return response


class SecurityHeadersMiddleware(Middleware):
    """Security headers middleware"""

    def process_response(self, response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response


class EnhancedStaticHandler:
    def __init__(self, directory, url_prefix="/static/", debug=False):
        self.directory = os.path.abspath(directory)
        self.url_prefix = url_prefix
        self.debug = debug
        self.file_cache = {}  # Cache for file content and metadata
        self.etag_cache = {}  # Separate ETag cache

    def _generate_content_hash(self, file_path):
        """Generate hash based on actual file content"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            return None

    def _generate_etag(self, file_path):
        """Generate ETag with content hash + modification time"""
        try:
            stat = os.stat(file_path)
            content_hash = self._generate_content_hash(file_path)
            if content_hash:
                # Combine content hash with mtime for strong ETag
                etag_data = f"{content_hash}-{stat.st_mtime}-{stat.st_size}"
                return f'"{hashlib.md5(etag_data.encode()).hexdigest()}"'
            else:
                # Fallback to weak ETag
                etag_data = f"{stat.st_mtime}-{stat.st_size}"
                return f'W/"{hashlib.md5(etag_data.encode()).hexdigest()}"'
        except Exception as e:
            logger.error(f"Error generating ETag for {file_path}: {e}")
            return None

    def _is_file_modified(self, file_path, cached_etag):
        """Check if file has been modified since last cache"""
        try:
            current_etag = self._generate_etag(file_path)
            return current_etag != cached_etag
        except Exception:
            return True  # Assume modified if can't determine

    def _get_cache_headers(self, file_path):
        """Get appropriate cache headers based on debug mode and file type"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        headers = {}

        if self.debug:
            # In debug mode, disable caching for dynamic content
            if ext in [".js", ".css", ".html", ".htm"]:
                headers.update(
                    {
                        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                        "Pragma": "no-cache",
                        "Expires": "0",
                    }
                )
            else:
                # For images and other assets, short cache
                headers["Cache-Control"] = "public, max-age=60"
        else:
            # Production mode - longer caching
            if ext in [".js", ".css"]:
                headers["Cache-Control"] = "public, max-age=86400"  # 1 day
            elif ext in [".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg"]:
                headers["Cache-Control"] = "public, max-age=604800"  # 1 week
            else:
                headers["Cache-Control"] = "public, max-age=3600"  # 1 hour

        return headers

    def serve_file(self, request, response, file_path):
        """Serve a static file with proper caching"""
        abs_file_path = os.path.join(self.directory, file_path)
        abs_file_path = os.path.normpath(abs_file_path)

        # Security check
        if not abs_file_path.startswith(self.directory):
            response.status_code = 403
            response.text = "Forbidden"
            logger.warning(f"Directory traversal attempt: {file_path}")
            return

        # Check if file exists
        if not os.path.isfile(abs_file_path):
            response.status_code = 404
            response.text = "Not found."
            return

        try:
            # Get file stats
            stat = os.stat(abs_file_path)

            # Generate ETag
            etag = self._generate_etag(abs_file_path)

            # Check If-None-Match header (ETag-based caching)
            if_none_match = request.environ.get("HTTP_IF_NONE_MATCH")
            if if_none_match and etag and if_none_match == etag and not self.debug:
                response.status_code = 304
                response.headers["ETag"] = etag
                return

            # Check If-Modified-Since header
            if_modified_since = request.environ.get("HTTP_IF_MODIFIED_SINCE")
            if if_modified_since and not self.debug:
                try:
                    from email.utils import parsedate_tz, mktime_tz

                    if_modified_timestamp = mktime_tz(parsedate_tz(if_modified_since))
                    if stat.st_mtime <= if_modified_timestamp:
                        response.status_code = 304
                        if etag:
                            response.headers["ETag"] = etag
                        return
                except (ValueError, TypeError):
                    pass

            # Determine content type
            content_type, encoding = mimetypes.guess_type(abs_file_path)
            if not content_type:
                content_type = "application/octet-stream"

            # Read file content
            with open(abs_file_path, "rb") as f:
                content = f.read()

            # Set response
            response.status_code = 200
            response.body = content
            response.content_type = content_type

            # Set headers
            response.headers.update(
                {
                    "Content-Length": str(len(content)),
                    "Last-Modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    ),
                    "Accept-Ranges": "bytes",
                }
            )

            if etag:
                response.headers["ETag"] = etag

            if encoding:
                response.headers["Content-Encoding"] = encoding

            # Add cache control headers
            cache_headers = self._get_cache_headers(abs_file_path)
            response.headers.update(cache_headers)

            # Add version parameter for cache busting in debug mode
            if self.debug:
                response.headers["X-File-Version"] = str(int(stat.st_mtime))

        except Exception as e:
            logger.error(f"Error serving static file {abs_file_path}: {e}")
            response.status_code = 500
            response.text = "Internal Server Error"