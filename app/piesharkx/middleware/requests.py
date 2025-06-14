import os, time
from datetime import datetime, timedelta, timezone

__all__ = ["CacheControl", "RequestHandler", "FormDataManager"]


class CacheControl:
    """Cache control implementation for static files"""

    def __init__(self, max_age=3600):
        self.max_age = max_age

    def get_headers(self):
        return [
            ("Cache-Control", f"max-age={self.max_age}, public"),
            ("Expires", self._get_expires_header()),
        ]

    def _get_expires_header(self):
        from email.utils import formatdate

        return formatdate(time.time() + self.max_age, localtime=False, usegmt=True)


class RequestHandler:
    """Base class for request handlers with middleware support"""

    def __init__(self):
        self.middlewares = []

    def add_middleware(self, middleware):
        self.middlewares.append(middleware)
        return self

    def process_request(self, request, response):
        for middleware in self.middlewares:
            request = middleware.process_request(request)
        return request

    def process_response(self, response):
        for middleware in reversed(self.middlewares):
            response = middleware.process_response(response)
        return response


class FormDataManager:
    """Manage form data to prevent duplicate submissions"""

    def __init__(self):
        self.processed_forms = {}  # Store processed form tokens
        self.form_data_cache = {}  # Cache form data temporarily

    def generate_form_token(self):
        """Generate unique form token"""
        import uuid

        return str(uuid.uuid4())

    def is_form_processed(self, token):
        """Check if form was already processed"""
        return token in self.processed_forms

    def mark_form_processed(self, token):
        """Mark form as processed"""
        self.processed_forms[token] = {"timestamp": datetime.now()}
        # Clean old tokens (older than 1 hour)
        cutoff = datetime.now() - timedelta(hours=1)
        self.processed_forms = {
            k: v for k, v in self.processed_forms.items() if v["timestamp"] > cutoff
        }
