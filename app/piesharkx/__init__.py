"""
Welcome to **PieShark** Framework

**PieShark** is a modern, lightweight WSGI-based Python web framework designed for developers who want power without complexity. 
Built with performance and security in mind, it offers everything you need to create robust web applications and APIs.
"""
from dotenv import load_dotenv
load_dotenv()
import os, sys

from .cli import cli
from .handler.endecryptions import (AdvancedCryptoSystem, 
    Base64_Token_128, Ciphertext_128, Magic_Data, 
    AESCipher, AUTH_TOKEN, AESCipher_2, AES, 
    base64, hashlib)
from .handler.error_handler import (
    Socket_Error, Do_Under, Typping, AbstractClass,
    Handlerr, ErrorHandler, HTTPException, BadRequest, 
    Unauthorized, Forbidden, NotFound, MethodNotAllowed, 
    InternalServerError, HTTPExceptions, PieSharkErrorMixin,
    error_handler_decorator, ErrorContext, ErrorLogger)
from .handler.handshake import NetworkScanner, NetworkServer
from .handler.requests_ansyc import REQUESTS
from .handler.obfuscator import JS_Obfuscator

from .middleware.mimet import (BLOCK_SIZE
    , TYPE_LOADS, mimetypes
    , MIMETypeHandler, FileWrapper)
from .middleware.limiter import RateLimiter
from .middleware.headerGuard import (Middleware
    , CORSMiddleware, SecurityHeadersMiddleware
    , EnhancedStaticHandler)
from .middleware.requests import CacheControl, RequestHandler, FormDataManager
from .middleware.memoryBrowser import (SecureSessionManager
    , SessionWrapper, ImprovedSessionManager)


from .configuration import config_pieshark, config
from .date_moduler import (utc_mktime, date_str, datetime_next
    , datetime_now, datetime_UTF, UTC_DATE_TIME, TimeStamp)
from .localcontex import (LocalProxy, Local, RequestContext
    , _lookup_req_object, _lookup_app_object)
from .logger import logger
from .blueprint import Blueprint
from .templates import (Templates, Jinja2_Base_Templates
    , allow_extent, read_file)
from .pydejs import PY_deJS
from .sessions import SESSION
from .cookies import CookieManajer, Cookie
from .printer import mainPrinter
from .main import (current_app, request
    , form, session, g as cookie, pieshark)

mainPrinter()