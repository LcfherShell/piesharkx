import re
import logging
from collections import OrderedDict
from typing import Optional, List, Dict, Callable, Any, Union, Pattern
from functools import wraps
import os
import threading
from .logger import logger

__all__ = ["Blueprint"]



class BlueprintError(Exception):
    """Base exception for Blueprint-related errors"""
    pass

class RouteConflictError(BlueprintError):
    """Raised when there's a route conflict"""
    pass

class InvalidRouteError(BlueprintError):
    """Raised when route configuration is invalid"""
    pass

class Blueprint:
    """Blueprint for organizing routes in PieShark framework"""
    
    # Class-level registry to track blueprint names
    _registry = set()
    _registry_lock = threading.Lock()
    
    def __init__(self, name: str, url_prefix: Optional[str] = None, 
                 static_folder: Optional[str] = None, template_folder: Optional[str] = None):
        """Initialize Blueprint
        
        Args:
            name: Blueprint name (must be unique)
            url_prefix: URL prefix for all routes in this blueprint
            static_folder: Static files folder for this blueprint
            template_folder: Template folder for this blueprint
            
        Raises:
            BlueprintError: If blueprint name is invalid or already exists
            ValueError: If folders don't exist or are invalid
        """
        # Validate blueprint name
        if not name or not isinstance(name, str):
            raise BlueprintError("Blueprint name must be a non-empty string")
        
        if not name.replace('_', '').replace('-', '').isalnum():
            raise BlueprintError("Blueprint name must contain only alphanumeric characters, hyphens, and underscores")
        
        # Ensure blueprint name is unique
        with self._registry_lock:
            if name in self._registry:
                raise BlueprintError(f"Blueprint '{name}' already exists")
            self._registry.add(name)
        
        self.name = name
        self._registered = False
        
        # Validate and normalize URL prefix
        self.url_prefix = self._validate_url_prefix(url_prefix)
        
        # Validate folder paths
        self.static_folder = self._validate_folder(static_folder, "static")
        self.template_folder = self._validate_folder(template_folder, "template")
        
        # Storage for routes and handlers
        self.routes: Dict[str, tuple] = OrderedDict()
        self.route_patterns: Dict[Pattern, tuple] = OrderedDict()
        self.before_request_hooks: List[Callable] = []
        self.after_request_hooks: List[Callable] = []
        self.error_handlers: Dict[int, Callable] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.debug(f"Blueprint '{name}' created with prefix '{self.url_prefix}'")
    
    def __del__(self):
        """Clean up blueprint registration when object is destroyed"""
        try:
            with self._registry_lock:
                self._registry.discard(self.name)
        except:
            pass  # Ignore errors during cleanup
    
    def _validate_url_prefix(self, url_prefix: Optional[str]) -> str:
        """Validate and normalize URL prefix"""
        if url_prefix is None:
            return ''
        
        if not isinstance(url_prefix, str):
            raise ValueError("URL prefix must be a string")
        
        # Remove leading/trailing whitespace
        url_prefix = url_prefix.strip()
        
        if not url_prefix:
            return ''
        
        # Validate URL prefix format
        if not re.match(r'^[a-zA-Z0-9/_-]+$', url_prefix):
            raise ValueError("URL prefix contains invalid characters")
        
        # Ensure url_prefix starts with / and doesn't end with /
        if not url_prefix.startswith('/'):
            url_prefix = '/' + url_prefix
        
        if url_prefix.endswith('/') and len(url_prefix) > 1:
            url_prefix = url_prefix.rstrip('/')
        
        # Prevent double slashes
        url_prefix = re.sub(r'/+', '/', url_prefix)
        
        return url_prefix
    
    def _validate_folder(self, folder: Optional[str], folder_type: str) -> Optional[str]:
        """Validate folder path"""
        if folder is None:
            return None
        
        if not isinstance(folder, str):
            raise ValueError(f"{folder_type} folder must be a string")
        
        folder = folder.strip()
        if not folder:
            return None
        
        # Security check: prevent path traversal
        if '..' in folder or folder.startswith('/'):
            raise ValueError(f"Invalid {folder_type} folder path: {folder}")
        
        # Check if folder exists (optional - create if needed)
        if not os.path.exists(folder):
            logger.warning(f"{folder_type} folder '{folder}' does not exist")
        
        return folder
    
    def _validate_route_path(self, path: str) -> str:
        """Validate route path"""
        if not isinstance(path, str):
            raise InvalidRouteError("Route path must be a string")
        
        if not path:
            raise InvalidRouteError("Route path cannot be empty")
        
        # Allow regex patterns starting with ^
        if path.startswith('^'):
            try:
                re.compile(path)
            except re.error as e:
                raise InvalidRouteError(f"Invalid regex pattern: {e}")
            return path
        
        # For normal paths, ensure they start with /
        if not path.startswith('/'):
            path = '/' + path
        
        # Validate path format
        if not re.match(r'^/[a-zA-Z0-9/_<>:-]*$', path):
            raise InvalidRouteError(f"Invalid route path format: {path}")
        
        return path
    
    def _validate_methods(self, methods: Optional[List[str]]) -> List[str]:
        """Validate HTTP methods"""
        if methods is None:
            return ["GET"]
        
        if not isinstance(methods, list):
            raise InvalidRouteError("Methods must be a list")
        
        if not methods:
            raise InvalidRouteError("Methods list cannot be empty")
        
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        normalized_methods = []
        
        for method in methods:
            if not isinstance(method, str):
                raise InvalidRouteError("HTTP method must be a string")
            
            method = method.upper().strip()
            if method not in valid_methods:
                raise InvalidRouteError(f"Invalid HTTP method: {method}")
            
            if method not in normalized_methods:
                normalized_methods.append(method)
        
        return normalized_methods
    
    def _check_route_conflict(self, full_path: str, pattern: Optional[Pattern] = None):
        """Check for route conflicts"""
        with self._lock:
            # Check exact path conflicts
            if full_path in self.routes:
                raise RouteConflictError(f"Route '{full_path}' already exists in blueprint '{self.name}'")
            
            # Check pattern conflicts
            if pattern:
                for existing_pattern in self.route_patterns:
                    if existing_pattern.pattern == pattern.pattern:
                        raise RouteConflictError(f"Route pattern '{pattern.pattern}' already exists in blueprint '{self.name}'")
    
    def route(self, path: str, methods: Optional[List[str]] = None):
        """Register a route handler in this blueprint
        
        Args:
            path: URL pattern to match
            methods: List of HTTP methods this route supports
            
        Raises:
            InvalidRouteError: If route configuration is invalid
            RouteConflictError: If route already exists
        """
        # Validate inputs
        path = self._validate_route_path(path)
        methods = self._validate_methods(methods)
        
        def wrapper(handler: Callable) -> Callable:
            if not callable(handler):
                raise InvalidRouteError("Route handler must be callable")
            
            with self._lock:
                # Combine url_prefix with route path
                if path == '/' and not self.url_prefix:
                    full_path = '/'
                elif path == '/':
                    full_path = self.url_prefix or '/'
                else:
                    full_path = self.url_prefix + path
                
                if path.startswith("^"):  # Regex pattern
                    # For regex patterns, adjust to include prefix
                    if self.url_prefix:
                        adjusted_pattern = f"^{self.url_prefix}{path[1:]}"
                    else:
                        adjusted_pattern = path
                    
                    try:
                        compiled_pattern = re.compile(adjusted_pattern)
                    except re.error as e:
                        raise InvalidRouteError(f"Invalid regex pattern: {e}")
                    
                    self._check_route_conflict(full_path, compiled_pattern)
                    self.route_patterns[compiled_pattern] = (handler, methods)
                    logger.debug(f"Regex route registered in blueprint '{self.name}': {adjusted_pattern} -> {handler.__name__}")
                else:
                    self._check_route_conflict(full_path)
                    self.routes[full_path] = (handler, methods)
                    logger.debug(f"Route registered in blueprint '{self.name}': {full_path} -> {handler.__name__}")
            
            # Add metadata to handler
            handler._blueprint_name = self.name
            handler._route_path = full_path
            handler._route_methods = methods
            
            return handler
        
        return wrapper
    
    def get(self, path: str):
        """Register a GET route handler"""
        return self.route(path, methods=["GET"])
    
    def post(self, path: str):
        """Register a POST route handler"""
        return self.route(path, methods=["POST"])
    
    def put(self, path: str):
        """Register a PUT route handler"""
        return self.route(path, methods=["PUT"])
    
    def delete(self, path: str):
        """Register a DELETE route handler"""
        return self.route(path, methods=["DELETE"])
    
    def patch(self, path: str):
        """Register a PATCH route handler"""
        return self.route(path, methods=["PATCH"])
    
    def head(self, path: str):
        """Register a HEAD route handler"""
        return self.route(path, methods=["HEAD"])
    
    def options(self, path: str):
        """Register an OPTIONS route handler"""
        return self.route(path, methods=["OPTIONS"])
    
    def before_request(self, func: Callable):
        """Register a function to execute before each request in this blueprint
        
        Args:
            func: Function to execute before request
            
        Raises:
            ValueError: If func is not callable
        """
        if not callable(func):
            raise ValueError("Before request hook must be callable")
        
        with self._lock:
            if func not in self.before_request_hooks:
                self.before_request_hooks.append(func)
                logger.debug(f"Before request hook registered in blueprint '{self.name}': {func.__name__}")
        
        return func
    
    def after_request(self, func: Callable):
        """Register a function to execute after each request in this blueprint
        
        Args:
            func: Function to execute after request
            
        Raises:
            ValueError: If func is not callable
        """
        if not callable(func):
            raise ValueError("After request hook must be callable")
        
        with self._lock:
            if func not in self.after_request_hooks:
                self.after_request_hooks.append(func)
                logger.debug(f"After request hook registered in blueprint '{self.name}': {func.__name__}")
        
        return func
    
    def error(self, code: Union[int, List[int]]):
        """Register an error handler for this blueprint
        
        Args:
            code: HTTP error code(s) to handle
            
        Raises:
            ValueError: If error code is invalid
        """
        # Normalize to list
        if isinstance(code, int):
            codes = [code]
        elif isinstance(code, list):
            codes = code
        else:
            raise ValueError("Error code must be an integer or list of integers")
        
        # Validate error codes
        for c in codes:
            if not isinstance(c, int) or c < 100 or c > 599:
                raise ValueError(f"Invalid HTTP error code: {c}")
        
        def wrapper(handler: Callable) -> Callable:
            if not callable(handler):
                raise ValueError("Error handler must be callable")
            
            with self._lock:
                for c in codes:
                    if c in self.error_handlers:
                        logger.warning(f"Overriding existing error handler for code {c} in blueprint '{self.name}'")
                    self.error_handlers[c] = handler
                    logger.debug(f"Error handler registered in blueprint '{self.name}': {c} -> {handler.__name__}")
            
            return handler
        
        return wrapper
    
    def get_routes(self) -> Dict[str, tuple]:
        """Get all routes registered in this blueprint (thread-safe)"""
        with self._lock:
            return self.routes.copy()
    
    def get_route_patterns(self) -> Dict[Pattern, tuple]:
        """Get all route patterns registered in this blueprint (thread-safe)"""
        with self._lock:
            return self.route_patterns.copy()
    
    def get_error_handlers(self) -> Dict[int, Callable]:
        """Get all error handlers registered in this blueprint (thread-safe)"""
        with self._lock:
            return self.error_handlers.copy()
    
    def clear_routes(self):
        """Clear all routes (useful for testing)"""
        with self._lock:
            self.routes.clear()
            self.route_patterns.clear()
            logger.debug(f"All routes cleared from blueprint '{self.name}'")
    
    def clear_hooks(self):
        """Clear all hooks (useful for testing)"""
        with self._lock:
            self.before_request_hooks.clear()
            self.after_request_hooks.clear()
            logger.debug(f"All hooks cleared from blueprint '{self.name}'")
    
    def clear_error_handlers(self):
        """Clear all error handlers (useful for testing)"""
        with self._lock:
            self.error_handlers.clear()
            logger.debug(f"All error handlers cleared from blueprint '{self.name}'")
    
    def is_registered(self) -> bool:
        """Check if blueprint is registered with an application"""
        return self._registered
    
    def _mark_registered(self):
        """Mark blueprint as registered (internal use)"""
        self._registered = True
    
    def __repr__(self) -> str:
        return f"Blueprint(name='{self.name}', url_prefix='{self.url_prefix}', routes={len(self.routes)})"
    
    def __str__(self) -> str:
        return f"Blueprint '{self.name}' with {len(self.routes)} routes"