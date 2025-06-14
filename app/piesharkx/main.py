import sys, inspect, os, mimetypes, re, requests, socket, json, time, logging, hashlib, ssl, signal, threading, uuid
from urllib.parse import parse_qs, urlparse
from functools import wraps
from datetime import datetime, timedelta
from parse import parse
from contextvars import copy_context
from webob import Request, Response
from webob.static import DirectoryApp, FileApp, FileIter
from webob.cookies import (
    RequestCookies,
    SAMESITE_VALIDATION,
    make_cookie,
    CookieProfile,
)
from webob.dec import wsgify
from webob import exc
import asyncio, cgi
from wsgiref.simple_server import make_server
from io import BytesIO
from typing import Union, Dict, List, Tuple, Any, Optional, Callable
from collections import defaultdict
from threading import Thread, Lock, RLock
from werkzeug.serving import run_simple
import concurrent.futures

from .blueprint import Blueprint
from .templates import read_file, read_file_byets
from .localcontex import RequestContext, LocalProxy, partial, _lookup_app_object, _lookup_req_object, _request_ctx_stack
try:
    from .configuration import config_pieshark
except:

    class config_pieshark:
        pass
from .logger import logger
from .middleware.mimet import *
from .middleware.limiter import *
from .middleware.headerGuard import *
from .middleware.requests import *
from .middleware.memoryBrowser import *
from .handler import OrderedDict, SelectType, create_secure_memory as Struct
from .handler.error_handler import PieSharkErrorMixin, ErrorHandler, HTTPExceptions as HTTPException, Handlerr as ERROR_MESSAGES
from .handler.endecryptions import AdvancedCryptoSystem
from .handler.handshake import Shake as handshakes

__all__ = ["current_app", "request", "form", "session", "g", "pieshark"]


ERROR_MESSAGES = ERROR_MESSAGES()
SAMESITE_VALIDATION = True


class AdvancedCryptoSystemShark:
    def __init__(self, app):
        self._AdvancedCryptoSystem = AdvancedCryptoSystem()
        try:
            if app.config.config.secret_key:
                key = app.config.config.secret_key
            else:
                key = app.secret_key
                logger.warning(
                    "There is no secret key in the app, salt will be created automatically"
                )
            self._salt = key
        except:
            self._salt = app.secret_key
        self._last_encrypted = None

    def __call__(self, value: str, types: str = "hybrid"):
        if types.lower() == "hybrid":
            self._last_encrypted = self._AdvancedCryptoSystem.hybrid_encrypt(
                value, self._salt
            )
        else:
            self._last_encrypted = self._AdvancedCryptoSystem.custom_base64_encrypt(
                value, self._salt
            )

    def __str__(self):
        return (
            self._last_encrypted.get(
                "hybrid_encrypted", self._last_encrypted.get("encrypted")
            )
            or None
        )

    def __repr__(self):
        return (
            self._last_encrypted.get(
                "hybrid_encrypted", self._last_encrypted.get("encrypted")
            )
            or None
        )

    def decode(self):
        decode = None
        if "hybrid_encrypted" in self._last_encrypted.keys():
            decode = self._AdvancedCryptoSystem.hybrid_decrypt(self._last_encrypted)
        else:
            decode = self._AdvancedCryptoSystem.custom_base64_decrypt(
                self._last_encrypted["encrypted"],
                self._last_encrypted["key"],
                self._last_encrypted["checksum"],
            )
        return decode


def limitSizes(app, size: int):
    limitSize = 0
    try:
        limitSize = app.config.config.limit_size_upload
    except:
        limitSize = 109715200
    if limitSize >= size:
        return True
    return False


def parse_custom_post(environ, max_mem=1024 * 1024):  # 1MB batas
    fs = cgi.FieldStorage(
        fp=environ["wsgi.input"],
        environ=environ,
        keep_blank_values=True,
        max_memorized=max_mem,
    )
    return fs

current_app = LocalProxy(partial(_lookup_app_object, 'app'))
request = LocalProxy(partial(_lookup_req_object, 'request'))
form = LocalProxy(partial(_lookup_req_object, 'form'))
session = LocalProxy(partial(_lookup_req_object, 'session'))
g = LocalProxy(partial(_lookup_req_object, 'g'))

Struct = Struct("pieshark_environ")

class pieshark(config_pieshark, PieSharkErrorMixin):
    """Enhanced PieShark framework implementation"""

    SAMESITE_VALIDATION = SAMESITE_VALIDATION

    def __init__(self, debug=False, secret_key=None, **kwargs):
        """Initialize the PieShark framework"""
        try:
            super().__init__(debug, **kwargs)
        except:
            pass
        self.routes = OrderedDict()
        self.route_patterns = OrderedDict()  # For regex patterns
        self.configt = Struct()
        self.headers = OrderedDict()
        self.environ = OrderedDict()
        self.static_file = OrderedDict()
        self.cookie = RequestCookies(self.environ)
        self.memory = Struct()
        self.request = Struct(method=self.method)
        self.forms = self.form
        self.debug = debug
        self.secret_key = secret_key or os.urandom(24).hex()


        # Blueprint support
        self.blueprints = OrderedDict()
        self.blueprint_hooks = {
            'before_request': {},
            'after_request': {},
            'error_handlers': {}
        }

        # Event hooks
        self.before_request_hooks = []
        self.after_request_hooks = []

        # Initialize components
        # Enhanced Session Configuration
        default_session_config = {
            'timeout': 3600,  # 1 hour
            'cookie_name': 'pieshark_session',
            'secure_cookies': False,
            'cleanup_interval': 300  # 5 minutes
        }
        
        if hasattr(self.config, "session"):
            default_session_config.update( self.config.session if hasattr(self.config, "session") else {})
        
        # Initialize Enhanced Session Manager
        self.session_manager = SecureSessionManager(
            secret_key=self.secret_key,
            session_timeout=default_session_config['timeout'],
            cookie_name=default_session_config['cookie_name'],
            secure_cookies=default_session_config['secure_cookies'],
            cleanup_interval=default_session_config['cleanup_interval']
        )
        self.form_manager = FormDataManager()  # commingsoon update

        self.rate_limiter = RateLimiter()
        self.request_handler = RequestHandler()

        # Add default middleware
        self.request_handler.add_middleware(SecurityHeadersMiddleware())

        # Event hooks
        self.before_request_hooks = []
        self.after_request_hooks = []

        # Static file cache
        self.static_cache = {}

        # Initialize the thread pool for handling requests
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        # Async support
        self._async_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="pieshark-async")
        self._loop = None
        self._async_lock = Lock()

        # Set up logging based on debug mode
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        
        if self.debug:
            caller_frame = inspect.stack()[-1]
            caller_file = os.path.basename(caller_frame.filename) or ""
            caller_file = caller_file.lower()
            if not (caller_file.startswith("app") and caller_file.split(".")[0] == "app"):
                logger.critical(f"Running foreign script {caller_file}")

        logger.info("PieShark framework initialized")

    def _get_or_create_event_loop(self):
        """Get or create event loop for async operations"""
        with self._async_lock:
            if self._loop is None or self._loop.is_closed():
                try:
                    self._loop = asyncio.get_event_loop()
                except RuntimeError:
                    self._loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._loop)
            return self._loop
        
    def _is_async_callable(self, func):
        """Check if a function is async (coroutine function)"""
        return (inspect.iscoroutinefunction(func) or inspect.iscoroutinefunction(getattr(func, '__call__', None))) and bool(func.__code__.co_flags & 0x80)

    def _run_async_in_thread(self, coro):
        """Run async coroutine in a separate thread with its own event loop"""
        # Simpan konteks dari thread utama
        import piesharkx.localcontex as lc

        try:
            current_ctx = lc._request_ctx_stack.current  # dari threading.local()
        except AttributeError:
            current_ctx = None

        def run_in_thread():
            if current_ctx:
                lc._request_ctx_stack.current = current_ctx  # inject ke thread baru

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
                # Bersihkan agar tidak bocor
                if hasattr(lc._request_ctx_stack, 'current'):
                    del lc._request_ctx_stack.current

        future = self._async_executor.submit(run_in_thread)
        return future.result()
    
    def _handle_async_result(self, func, *args, **kwargs):
        """Handle both sync and async functions automatically"""
        if self._is_async_callable(func):
            try:
                # Create coroutine
                coro = func(*args, **kwargs)
                # Run it in a thread with its own event loop
                return self._run_async_in_thread(coro)
            except Exception as e:
                logger.error(f"Error in async handler: {e}")
                raise
        else:
            # Regular synchronous function
            return func(*args, **kwargs)
        
    def __call__(self, environ, start_response):
        """WSGI application interface with LocalProxy support"""
        # Create request context and push to stack
        with RequestContext(self, environ) as ctx:
            try:
                # Set current context with your existing logic
                self._request_ctx = ctx
                request_obj = Request(environ)
                self.environ = environ
                
                # Set up session from your session manager
                session_data = self.session_manager.load_session(request_obj) if hasattr(self, 'session_manager') else {}
                ctx.session = session_data
                ctx.request = request_obj
                
                # # Get client IP for rate limiting (existing logic)
                # x_forwarded_for = self.environ.get("HTTP_X_FORWARDED_FOR")
                # client_ip = (
                #     x_forwarded_for.split(",")[0].strip()
                #     if x_forwarded_for
                #     else self.environ.get("REMOTE_ADDR", "0.0.0.0")
                # )

                time.sleep(0.08)
                # Check rate limit (existing logic)
                if not self.rate_limiter.check_limit(request_obj):
                    response = Response(status=429, body="Too Many Requests")
                    return response(self.environ, start_response)

                # Extract the request method (existing logic)
                method = request_obj.method

                # Process form data for POST and PUT requests (existing logic)
                if method in ["POST", "PUT", "GET"]:
                    self.method = method
                    if method in ["POST"]:
                        form = dict(request_obj.POST) if hasattr(request_obj, 'POST') else {}
                    else:
                        form = dict({})

                    # Handle file uploads (existing logic)
                    try:
                        if hasattr(request_obj, 'params'):
                            for x in request_obj.params:
                                inpuform = request_obj.params.get(x)

                                # Jika file
                                if hasattr(inpuform, "filename") and hasattr(inpuform, "file"):
                                    files = inpuform.file
                                    filedsFiles = files.read()
                                    try:
                                        filedsFiles = filedsFiles.decode()
                                    except:
                                        pass
                                    form[str(x)] = [inpuform.filename, filedsFiles]

                                # Jika string biasa
                                elif isinstance(inpuform, str):
                                    # Enkripsi
                                    encryptions = AdvancedCryptoSystemShark(self)
                                    encryptions(inpuform)
                                    form[str(x)] = encryptions  # simpan hasil enkripsi

                    except Exception as e:
                        logger.error(f"Error handling file upload: {e}")
                    
                    self.form = form
                    self._handler_files
                    
                    ctx.form = self.form if form else form

                # Execute before request hooks (modified to work with LocalProxy)
                for hook in self.before_request_hooks:
                    if hook.__code__.co_argcount > 0:
                        result = self._handle_async_result(hook, request_obj)
                    else:
                        result = self._handle_async_result(hook)
                    if result is not None:
                        return self._make_response(result)(environ, start_response)
                    time.sleep(0.02)

                # Process the request
                response = self.handle_request(request_obj)
                
                # Execute after request hooks (modified to work with LocalProxy)
                for hook in self.after_request_hooks:
                    if hook.__code__.co_argcount > 0:
                        result = self._handle_async_result(hook, response)
                    else:
                        result = self._handle_async_result(hook)
                    response = result or response
                    time.sleep(0.02)

                # Process the response through middleware (existing logic)
                if hasattr(self, 'request_handler'):
                    response = self.request_handler.process_response(response)

                # Add server identification header (existing logic)
                response.headers["Server"] = "PieShark/1.0"

                # Apply custom headers (existing logic)
                try:
                    if self.headers:
                        for key, value in self.headers.items():
                            response.headers[key] = value
                except Exception as e:
                    logger.error(f"Error setting headers: {e}")
                
                # Save session with enhanced security
                self.session_manager.save_session(request_obj, response)

                return response(environ, start_response)
                
            except Exception as e:
                if self.debug:
                    import traceback
                    error_response = self._make_response(
                        f"Server Error: {str(e)}\n\n{traceback.format_exc()}", 500
                    )
                else:
                    error_response = self._make_response("Internal Server Error", 500)
                
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error handling request: {e}", exc_info=True)
                else:
                    logger.error(f"Error handling request: {e}", exc_info=True)
                return error_response(environ, start_response)

    def _make_response(self, rv, status=200):
        """Convert return value to Response object"""
        if isinstance(rv, str):
            return Response(rv, status=status)
        elif isinstance(rv, dict):
            response = Response(status=status)
            response.content_type = 'application/json'
            response.data = json.dumps(rv).encode('utf-8')
            return response
        elif isinstance(rv, tuple):
            if len(rv) == 2:
                rv, status = rv
            elif len(rv) == 3:
                rv, status, headers = rv
            return self._make_response(rv, status)
        return rv
    
    def __getitem__(self, params):
        """Get item implementation"""
        return self.__dict__

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass

    def route(self, path, methods=None):
        """Register a route handler

        Args:
            path: URL pattern to match
            methods: List of HTTP methods this route supports
        """
        methods = methods or ["GET"]

        def wrapper(handler):
            # Store original handler info for async detection
            original_handler = handler
            
            # Create async-aware wrapper
            @wraps(handler)
            def async_wrapper(*args, **kwargs):
                return self._handle_async_result(original_handler, *args, **kwargs)
            
            # Preserve original function attributes
            async_wrapper._is_async_capable = True
            async_wrapper._original_handler = original_handler
            
            if path.startswith("^"):  # Regex pattern
                self.route_patterns[re.compile(path)] = (async_wrapper, methods)
            else:
                self.routes[path] = (async_wrapper, methods)
            
            return handler  # Return original handler for user reference

        return wrapper

    def get(self, path):
        """Register a GET route handler"""
        return self.route(path, methods=["GET"])

    def post(self, path):
        """Register a POST route handler"""
        return self.route(path, methods=["POST"])

    def put(self, path):
        """Register a PUT route handler"""
        return self.route(path, methods=["PUT"])

    def delete(self, path):
        """Register a DELETE route handler"""
        return self.route(path, methods=["DELETE"])

    def cleanup(self):
        """Clean up resources when server shuts down"""
        logger.info("Cleaning up PieShark resources...")
        # Shutdown async executor
        if hasattr(self, '_async_executor'):
            self._async_executor.shutdown(wait=True)
        # Close event loop
        if hasattr(self, '_loop') and self._loop and not self._loop.is_closed():
            try:
                self._loop.close()
            except:
                pass

        # Clear all routes and handlers
        self.routes.clear()
        self.route_patterns.clear()

        # Clear static file cache
        self.static_cache.clear()
        self.static_file.clear()

        # Clear headers and environment
        self.headers.clear()
        self.environ.clear()

        # Reset memory/form data
        if hasattr(self.memory, "update_dict"):
            self.memory.reset_to_original()

        # Clear sessions
        if hasattr(self.session_manager, "sessions"):
            self.session_manager.sessions.clear()

        # Shutdown thread pool
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)

    def error(self, code):
        """Register an error handler with async support"""
        def wrapper(handler):
            # Create async-aware error handler
            @wraps(handler)
            def async_error_wrapper(*args, **kwargs):
                return self._handle_async_result(handler, *args, **kwargs)
            
            self.error_handlers[code] = async_error_wrapper
            return handler
        return wrapper

    def default_response(self, response):
        """Default 404 response"""
        response.status_code = 404
        response.text = "Not found."
        logger.info(f"404 Not Found: {self.environ.get('PATH_INFO')}")

    def find_handler(self, request_path):
        """Find a handler for the request path"""
        # First try exact matches
        for path, (handler, methods) in self.routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler, parse_result.named, methods

        # Then try regex patterns
        for pattern, (handler, methods) in self.route_patterns.items():
            match = pattern.match(request_path)
            if match:
                return handler, match.groupdict(), methods

        return None, None, None

    @property
    def _handler_files(self):
        pass

    @_handler_files.setter
    def _handler_files(self, filelike):
        if "wsgi.file_wrapper" in self.environ:
            self.environ["wsgi.file_wrapper"](filelike, 81920)
        else:
            self.environ["wsgi.file_wrapper"] = FileWrapper

    def handle_request(self, request_obj):
        """Process the request and generate a response with LocalProxy support"""
        response = Response()

        handler, kwargs, methods = self.find_handler(request_path=request_obj.path)

        if handler is not None:
            # Check if the method is allowed
            if methods and request_obj.method not in methods:
                response.status_code = 405
                response.text = "Method Not Allowed"
                if hasattr(self, 'logger'):
                    self.logger.warning(f"Method not allowed: {request_obj.method} for {request_obj.path}")
                else:
                    logger.warning(f"Method not allowed: {request_obj.method} for {request_obj.path}")
                return response

            try:
                result = None

                if inspect.isclass(handler):
                    handler_instance = handler()
                    handler_method = getattr(handler_instance, request_obj.method.lower(), None)
                    if handler_method is None:
                        raise AttributeError("Method not allowed", request_obj.method)
                    # Call handler with async support
                    result = self._handle_async_result(handler_method, **kwargs)
                else:
                    # Call handler with async support
                    result = self._handle_async_result(handler, **kwargs)

                timenow = datetime.now()
                if request_obj.method == "POST":
                    response = self.__clear_browser_cache_headers(response, timenow)

                # Handle return values (existing logic)
                if result is not None:
                    if isinstance(result, Response):
                        response = result
                    elif isinstance(result, str):
                        response.text = result
                    elif isinstance(result, dict):
                        response.content_type = "application/json"
                        response.text = json.dumps(result)
                    elif isinstance(result, (list, tuple)):
                        response.content_type = "application/json"
                        response.text = json.dumps(result)
                    elif hasattr(result, "__str__"):
                        response.body = result

                response.status_code = 200
            except Exception as e:
                
                if self.debug:
                    import traceback
                    errormsg = f"Server Error: {str(e)}\n\n{traceback.format_exc()}"
                    response = self.abort(500, errormsg)
                    response.status_code = 500
                else:
                    response = self.abort(500, "Internal Server Error")
                    response.status_code = 500
                    response.text = "Internal Server Error"
                    
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error handling request: {e}", exc_info=True)
                else:
                    logger.error(f"Error handling request: {e}", exc_info=True)
        else:
            self.default_response(response)
        
        time.sleep(0.02)
        return response

    def __clear_browser_cache_headers(self, response, timesafter: datetime):
        """Add headers to prevent browser caching"""
        timenow = datetime.now()
        before = response.headers
        calculate = timenow - timesafter
        if calculate.total_seconds() > 40:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        response.headers = before
        return response

    def loads_files(self, file_path):
        """Determine content type and encoding for a file"""
        try:
            # Check if static directory is specified in environment
            if os.environ.get("static"):
                root = os.environ.get("static")
                file_path = os.path.join(root, file_path)
                if not os.path.isfile(file_path):
                    logger.warning(f"Warning: file {file_path} not found")
        except Exception as e:
            logger.error(f"Error loading file path: {e}")

        # Get file extension and determine content type
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lstrip(".").lower()

        # Try our custom mapping first
        if file_extension in TYPE_LOADS:
            content_type = TYPE_LOADS[file_extension]
        else:
            # Fall back to mimetypes library
            content_type, content_encoding = MIMETypeHandler.get_mime_type(file_path)
            if not content_type:
                # Default to octet-stream if unknown
                content_type = "application/octet-stream"

        # Get content encoding
        _, content_encoding = MIMETypeHandler.get_mime_type(file_path)

        return content_type, content_encoding

    @property
    def _handle_files(self):
        """Property for file handling"""
        pass

    @_handle_files.setter
    def _handle_files(self, filelike):
        """Set up file wrapper in WSGI environment"""
        if "wsgi.file_wrapper" in self.environ:
            self.environ["wsgi.file_wrapper"](filelike, 8192)
        else:
            self.environ["wsgi.file_wrapper"] = FileWrapper

    @property
    def method(self):
        """Get request method"""
        pass

    @method.setter
    def method(self, meth:str):
        """Set request method"""
        paths = {
            "GET": "GET",
            "POST": "POST",
            "PUT": "PUT",
            "DELETE": "DELETE",
            "OPTIONS": "OPTIONS",
        }
        if meth in paths:
            params = paths.get(meth)
        else:
            params = "GET"  # Default to GET for unknown methods

        method = {"method": params}
        if self.request.safe_get(params, 1):
            self.request.dell_dict("method")
        try:
            self.request.update_dict = method
        except:
            self.request.insert_dict = method

    @property
    def form(self):
        """Get form data"""
        return self.memory

    @form.setter
    def form(self, data):
        """Set form data"""
        try:
            self.memory.insert_dict = data
        except:
            self.memory.reset_to_original()
            self.memory.insert_dict = data

    @property
    def header(self):
        """Get headers"""
        pass

    @header.setter
    def header(self, params):
        """Set headers"""
        if isinstance(params, tuple) and len(params) == 2:
            self.headers[params[0]] = params[1]
        elif isinstance(params, list):
            if len(params) == 2:
                self.headers[params[0]] = params[1]
        elif isinstance(params, dict):
            self.headers.update(params)
        else:
            raise TypeError("Headers must be provided as tuple, list, or dict")

    @property
    def cookies(self):
        """Get cookies"""
        return self.cookie

    @cookies.setter
    def cookies(self, cookie):
        """Set cookies"""
        self.cookies.update(cookie)

    def set_cookie(
        self,
        name,
        value,
        max_age=None,
        expires=None,
        path="/",
        domain=None,
        secure=False,
        httponly=False,
        samesite=None,
    ):
        """Set a cookie with detailed parameters"""
        time.sleep(0.02)
        cookie = make_cookie(
            name,
            value,
            max_age=max_age,
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
        )
        self.header = ("Set-Cookie", cookie)
        return self

    def before_request(self, func):
        """Register a function to execute before each request with async support"""
        # Create async-aware wrapper
        @wraps(func)
        def async_hook_wrapper(*args, **kwargs):
            return self._handle_async_result(func, *args, **kwargs)
        
        self.before_request_hooks.append(async_hook_wrapper)
        return func

    def after_request(self, func):
        """Register a function to execute after each request with async support"""
        # Create async-aware wrapper
        @wraps(func)
        def async_hook_wrapper(*args, **kwargs):
            return self._handle_async_result(func, *args, **kwargs)
            
        self.after_request_hooks.append(async_hook_wrapper)
        return func

    def json_response(self, data, status=200):
        """Helper method to create JSON responses"""
        response = Response(content_type="application/json", status=status)
        response.body = json.dumps(data).encode("utf-8")
        return response

    def redirect(self, location, status=302):
        """Helper method to create redirect responses"""
        response = self._make_response("", status=status)
        time.sleep(0.12)
        response.location = location
        return response
    

    def _generate_etag(self, file_path):
        """Generate an ETag for a file based on its modification time and size"""
        stat = os.stat(file_path)
        etag_base = f"{stat.st_mtime}-{stat.st_size}"
        return hashlib.md5(etag_base.encode()).hexdigest()

    def static(self, directory, url_prefix="/static/"):
        """Serve static files with basic error handling and optional URL prefix."""
        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        directory = os.path.abspath(directory)
        url_prefix = "/" + url_prefix.strip("/") + "/"
        static_handler = EnhancedStaticHandler(directory, url_prefix, self.debug)
        @self.route(f"{url_prefix}"+"{path}", methods=["GET"])
        def static(path):
            response = self._make_response("Not Found.", status=200)
            if not path:
                response.status_code = 404
                response.text = "Not Found."
                return
            static_handler.serve_file(request, response, path)
            return response

        logger.info(f"Serving static files from {directory} at {url_prefix}")
        return self

    def register_blueprint(self, blueprint, **options):
        """Register a blueprint with the application
        
        Args:
            blueprint: Blueprint instance to register
            **options: Additional options for blueprint registration
        """
        if not isinstance(blueprint, Blueprint):
            raise TypeError("Expected Blueprint instance")
        
        if blueprint.name in self.blueprints:
            raise ValueError(f"Blueprint '{blueprint.name}' already registered")
        
        # Store blueprint reference
        self.blueprints[blueprint.name] = blueprint
        
        # Register all routes from blueprint
        for path, (handler, methods) in blueprint.routes.items():
            self.routes[path] = (handler, methods)
        
        # Register regex patterns from blueprint
        for pattern, (handler, methods) in blueprint.route_patterns.items():
            self.route_patterns[pattern] = (handler, methods)
        
        # Store blueprint hooks
        self.blueprint_hooks['before_request'][blueprint.name] = blueprint.before_request_hooks
        self.blueprint_hooks['after_request'][blueprint.name] = blueprint.after_request_hooks
        self.blueprint_hooks['error_handlers'][blueprint.name] = blueprint.error_handlers
        
        # Register static folder if specified
        if blueprint.static_folder:
            static_url = f"/{blueprint.name}/static/"
            if blueprint.url_prefix:
                static_url = f"{blueprint.url_prefix}/static/"
            self.static(blueprint.static_folder, static_url)
        
        logger.info(f"Blueprint '{blueprint.name}' registered with {len(blueprint.routes)} routes")

    def get_blueprint(self, name):
        """Get a registered blueprint by name"""
        return self.blueprints.get(name)
    
    def run(self, host="0.0.0.0", port=80, ssl_context=None, workers=1, threaded=True):
        """Run the WSGI server

        Args:
            host: Host address to bind to
            port: Port to listen on
            ssl_context: SSL context for HTTPS
            workers: Number of worker processes
            threaded: Enable multi-threading
        """

        def signal_handler(signum, frame):
            """Handle shutdown signals"""
            logger.info(f"Received signal {signum}, shutting down...")
            self.cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info(f"Starting server on {host}:{port}")

        # Perform handshake
        handshake = handshakes()
        handshake.response(host=host, port=port)
        if handshake.saving == "ERROR URL" or handshake.saving == "Private APP":
            try:
                if ssl_context:
                    logger.info("Starting HTTPS server")
                    return run_simple(
                        host,
                        port,
                        self,
                        ssl_context=ssl_context,
                        processes=workers,
                        threaded=threaded,
                    )
                else:
                    logger.info("Starting HTTP server")
                    return run_simple(
                        host, port, self, processes=workers, threaded=threaded
                    )
            except Exception as e:
                logger.error(f"Error starting Werkzeug server: {e}")
                try:
                    logger.info("Falling back to wsgiref server")
                    if workers > 1:
                        logger.warning(
                            "wsgiref server does not support multiple processes"
                        )

                    server = make_server(host, port, self)

                    # If SSL is requested and wsgiref is used, wrap the socket
                    if ssl_context:
                        server.socket = ssl_context.wrap_socket(
                            server.socket, server_side=True
                        )

                    return server.serve_forever()
                except Exception as e:
                    logger.critical(f"Could not start server: {e}")
                    raise
            finally:
                # Ensure cleanup happens
                self.configt.reset_to_original()
                self.memory.reset_to_original()
                self.request.reset_to_original()
                self.forms.reset_to_original()
                self.cleanup()
        else:
            ERROR_MESSAGES.Socket_Error()