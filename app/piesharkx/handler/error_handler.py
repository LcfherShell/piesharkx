from abc import ABC, ABCMeta, abstractmethod
import logging, os, sys, traceback, inspect, asyncio, re
from datetime import datetime
import json, html
from webob import Response
from typing import Dict, Optional, Callable, Any, Union
from http import HTTPStatus

from ..logger import logger

__all__ = [
    'ErrorHandler',
    'HTTPException',
    'BadRequest',
    'Unauthorized', 
    'Forbidden',
    'NotFound',
    'MethodNotAllowed',
    'InternalServerError',
    'HTTPExceptions',
    'PieSharkErrorMixin',
    'create_error_handler',
    'handle_404',
    'handle_500',
    'error_handler_decorator',
    'ErrorContext',
    'ErrorLogger'
]

class Socket_Error(Exception):
    pass

class Do_Under(NameError):
    pass

class Typping(TypeError):
    pass

class AbstractClass:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def Socket_Error(self):
        raise Socket_Error(self)

    @abstractmethod
    def Name_Error(self):
        raise Do_Under(self)

    @abstractmethod
    def Typ_Error(self):
        raise Typping(self)

    @abstractmethod
    def get_error(self):
        type_, value_, traceback_ = sys.exc_info()
        logger.error("".join(traceback.format_exception(type_, value_, traceback_)))

class Handlerr(AbstractClass):
    def __init__(self):
        super(Handlerr, self).__init__()

class ErrorHandler:
    """Advanced error handler for PieShark framework with clean error display"""
    
    def __init__(self, debug: bool = True, app_name: str = "PieShark App"):
        """Initialize ErrorHandler

        Args:
            debug: Enable debug mode with detailed error information
            app_name: App name to display on error pages
        """
        self.debug = debug
        self.app_name = app_name
        self.custom_error_handlers: Dict[int, Callable] = {}
        self.custom_exception_handlers: Dict[type, Callable] = {}
        caller_frame = inspect.stack()[-1]
        caller_file = os.path.dirname(caller_frame.filename)
        self.templates = self._find_like_template_regex(caller_file)
        # Pesan HTTP status yang lebih user-friendly
        self.status_messages = {
            400: "Invalid Request",
            401: "Unauthorized",
            403: "Access Denied",
            404: "Page Not Found",
            405: "Method Not Allowed",
            408: "Request Timeout",
            413: "Data Too Large",
            429: "Too Many Requests",
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Gateway Problem",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
    
    def register_error_handler(self, status_code: int, handlers: Callable):
        """Register custom error handler untuk status code tertentu"""
        if not isinstance(status_code, int) or status_code < 100 or status_code > 599:
            raise ValueError(f"Invalid HTTP status code: {status_code}")
        
        if not callable(handler):
            raise ValueError("Error handler must be callable")
        
        self.custom_error_handlers[status_code] = handlers
        logger.debug(f"Custom error handler registered for status code {status_code}")
    
    def register_exception_handler(self, exception_type: type, handlers: Callable):
        """Register custom exception handler untuk tipe exception tertentu"""
        if not isinstance(exception_type, type) or not issubclass(exception_type, Exception):
            raise ValueError("Exception type must be a subclass of Exception")
        
        if not callable(handler):
            raise ValueError("Exception handler must be callable")
        
        self.custom_exception_handlers[exception_type] = handlers
        logger.debug(f"Custom exception handler registered for {exception_type.__name__}")

    def _find_like_template_regex(self, start_path):
        pattern = re.compile(r'template', re.IGNORECASE)
        for root, dirs, files in os.walk(start_path):
            for d in dirs:
                if pattern.search(d):  # cocokkan nama folder yang mengandung 'template'
                    template_path = os.path.join(root, d)
                    parent_path = os.path.dirname(template_path)
                    return parent_path
        return None

    def handle_error(self, error: Union[Exception, int], request_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Method utama untuk handling error
        
        Args:
            error: Exception instance atau HTTP status code
            request_data: Informasi request (opsional)
            
        Returns:
            Dict berisi data response error
        """
        
        try:
            for exc_type, handler in self.custom_exception_handlers.items():
                if isinstance(error, exc_type):
                    return handler(error, request_data)

            # Fallback
            status_code = self._get_status_code(error, request_data)
            #message = self._get_user_message(error, request_data)
            templates = os.path.join(self.templates, f"{status_code}.shark") if self.templates else None
            if templates:
                if os.path.isfile(templates):
                    from ..templates import Templates
                    body = Templates(templates)
                    return {
                        "status_code": status_code,
                        "body": body,
                        "content_type": "text/html" if not self._wants_json(request_data) else "application/json",
                        'headers': {'X-Error-Type': 'Exception'}
                    }
                return self._handle_http_error(status_code, request_data)
            elif isinstance(error, Exception):
                return self._handle_exception(error, request_data)
            else:
                return self._handle_http_error(500, request_data)
        except Exception as e:
            logger.critical(f"Error dalam error handler: {e}")
            return self._get_fallback_error_response()
        
    def _wants_json(self, request_data):
        if not request_data:
            return False
        accept = request_data.get("headers", {}).get("Accept", "")
        return "application/json" in accept

    def _get_status_code(self, exception, request_data):
        if hasattr(exception, 'status_code'):
            return exception.status_code

        if isinstance(exception, AttributeError):
            if "session" in str(exception).lower():
                return 400
        if isinstance(exception, ValueError):
            return 400
        if isinstance(exception, KeyError):
            return 400
        if isinstance(exception, PermissionError):
            return 403
        return 500

    def _get_user_message(self, exception, request_data):
        msg = str(exception)
        if isinstance(exception, AttributeError) and "session" in msg.lower():
            return "Session does not have the requested attribute. Make sure you are logged in." 
        if isinstance(exception, KeyError):
            return "The requested key was not found." 
        if isinstance(exception, ValueError):
            return "Invalid input." 
        if isinstance(exception, PermissionError):
            return "You do not have permission for this action." 
        return "An unexpected error occurred."
    
    def _handle_http_error(self, status_code: int, request_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle HTTP status code errors"""
        # Cek custom handler
        if status_code in self.custom_error_handlers:
            try:
                return self.custom_error_handlers[status_code](status_code, request_data)
            except Exception as e:
                logger.error(f"Custom error handler gagal: {e}")
        
        # Generate default error response
        status_message = self.status_messages.get(status_code, "Error Tidak Dikenal")
        
        error_data = {
            'status_code': status_code,
            'status_message': status_message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'request_data': request_data or {}
        }
        
        if self.debug:
            error_data['debug_info'] = {
                'python_version': sys.version,
                'traceback': traceback.format_stack()
            }
        
        html_content = self._generate_modern_error_html(error_data)
        
        return {
            'status_code': status_code,
            'content_type': 'text/html',
            'body': html_content,
            'headers': {'X-Error-Type': 'HTTP'}
        }
    
    def _handle_exception(self, exception: Exception, request_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle Python exceptions"""
        exception_type = type(exception)
        
        # Cek custom exception handler
        for exc_type, handler in self.custom_exception_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    return handler(exception, request_data)
                except Exception as e:
                    logger.error(f"Custom exception handler gagal: {e}")
                    break
        
        # Tentukan HTTP status code berdasarkan tipe exception
        status_code = self._get_status_code_from_exception(exception)
        
        error_data = {
            'status_code': status_code,
            'status_message': self.status_messages.get(status_code, "Kesalahan Server Internal"),
            'exception_type': exception_type.__name__,
            'exception_message': str(exception),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'request_data': request_data or {}
        }
        
        if self.debug:
            error_data['debug_info'] = {
                'python_version': sys.version,
                'traceback': traceback.format_exc(),
                'exception_args': exception.args,
                'exception_module': exception_type.__module__
            }
        
        # Log exception
        logger.error(f"Unhandled exception: {exception_type.__name__}: {exception}", 
                    exc_info=True)
        
        html_content = self._generate_modern_error_html(error_data)
        
        return {
            'status_code': status_code,
            'content_type': 'text/html',
            'body': html_content,
            'headers': {'X-Error-Type': 'Exception'}
        }
    
    def _get_status_code_from_exception(self, exception: Exception) -> int:
        """Map exception types ke HTTP status codes"""
         # Spesifik untuk session attribute error
        if isinstance(exception, AttributeError) and "session" in str(exception).lower():
            return 400  # atau 422 jika mau dianggap 'Unprocessable Entity'
        
        exception_mapping = {
            FileNotFoundError: 404,
            PermissionError: 403,
            ValueError: 400,
            TypeError: 400,
            KeyError: 400,
            AttributeError: 500,
            ImportError: 500,
            ConnectionError: 502,
            TimeoutError: 504,
        }

        if hasattr(exception, 'status_code'):
            return exception.status_code

        for exc_type, status_code in exception_mapping.items():
            if isinstance(exception, exc_type):
                return status_code

        return 500
    
    def _generate_modern_error_html(self, error_data: Dict[str, Any]) -> str:
        """Generate halaman error HTML modern dan responsif"""
        status_code = error_data['status_code']
        status_message = error_data['status_message']
        
        # Sanitize data untuk HTML output
        safe_data = self._sanitize_for_html(error_data)
        
        # Template HTML modern
        html_template = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status_code} {status_message} - {app_name}</title>
    <style>
        {css_styles}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-content">
            <div class="error-icon">
                {error_icon}
            </div>
            
            <div class="error-header">
                <h1 class="error-code">{status_code}</h1>
                <h2 class="error-title">{status_message}</h2>
            </div>
            
            <div class="error-description">
                <p>{error_description}</p>
            </div>
            
            <div class="error-actions">
                <button onclick="history.back()" class="btn btn-primary">Back</button>
                <button onclick="location.reload()" class="btn btn-secondary">Reload</button>
                <a href="/" class="btn btn-outline">Home</a>
            </div>
            
            {debug_section}
            
            <div class="error-footer">
                <div class="footer-content">
                    <p class="timestamp">Time: {timestamp}</p>
                    <p class="powered-by">Powered by <strong>{app_name}</strong></p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {javascript}
    </script>
</body>
</html>
        '''
        
        # Generate komponen-komponen
        error_description = self._get_friendly_error_description(error_data)
        error_icon = self._get_error_icon(status_code)
        debug_section = self._generate_debug_section(safe_data) if self.debug else ""
        css_styles = self._get_modern_error_css()
        javascript = self._get_error_page_js()
        
        return html_template.format(
            status_code=status_code,
            status_message=html.escape(status_message),
            app_name=html.escape(self.app_name),
            error_description=error_description,
            error_icon=error_icon,
            debug_section=debug_section,
            timestamp=html.escape(safe_data['timestamp']),
            css_styles=css_styles,
            javascript=javascript
        )
    
    def _get_error_icon(self, status_code: int) -> str:
        """Get SVG icon berdasarkan status code"""
        icons = {
            404: '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
                <path d="M9 9l6 6"></path>
                <path d="m15 9-6 6"></path>
            </svg>''',
            403: '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <circle cx="12" cy="16" r="1"></circle>
                <path d="m7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>''',
            500: '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>'''
        }
        
        return icons.get(status_code, icons[500])
    
    def _get_friendly_error_description(self, error_data: Dict[str, Any]) -> str:
        """Generate deskripsi error yang user-friendly"""
        status_code = error_data['status_code']
        
        # Cek apakah ada custom description dari abort() atau exception message
        custom_description = None
        
        # 1. Cek custom_description dari request_data (dari abort method)
        request_data = error_data.get('request_data', {})
        if isinstance(request_data, dict) and 'custom_description' in request_data:
            custom_description = request_data['custom_description']
        
        # 2. Cek exception_message jika ada
        elif 'exception_message' in error_data and error_data['exception_message']:
            custom_description = error_data['exception_message']
        
        # Default descriptions berdasarkan status code
        default_descriptions = {
            400: "The request you sent could not be understood by the server. Please check the data you entered.",
            401: "You need to log in first to access this page.",
            403: "Sorry, you do not have permission to access this page.",
            404: "The page you are looking for cannot be found. It may have been moved or deleted.",
            405: "The method you used is not allowed for this page.",
            408: "Your request took too long. Please try again.",
            413: "The data you sent was too large for the server to process.",
            429: "You have sent too many requests. Please wait a moment and try again.",
            500: "There was an error on the server. Our team is working on this issue.",
            501: "The feature you requested is not available yet.",
            502: "The server is having trouble communicating with another service.",
            503: "The service is under maintenance or overloaded. Please try again later.",
            504: "The server took too long to respond."
        }
        
        main_description = ""

        # Jika ada custom description dari abort(), tambahkan deskripsi default di bawahnya
        if custom_description and status_code in default_descriptions:
            additional_info = f"<div class='additional-info'><small><strong>Additional Information:</strong><br>{default_descriptions[status_code]}</small></div>"
            main_description = additional_info if custom_description == None else "<small><strong>Error Message:</strong></small><br>"
        
        # Add exception information if present and in debug mode
        if 'exception_type' in error_data and self.debug:
            exception_info = f"<div class='exception-info'><strong>Technical Details:</strong> {html.escape(error_data['exception_type'])}"
            if error_data.get('exception_message'):
                exception_info += f"<br><em>{html.escape(error_data['exception_message'])}</em>"
            exception_info += "</div>"
            main_description += exception_info if custom_description == None else ""
        # Gunakan custom description jika ada, jika tidak gunakan default
        if custom_description:
            main_description += f"<pre class='messages-error'>{html.escape(custom_description)}</pre>"
        return main_description
    
    def _generate_debug_section(self, error_data: Dict[str, Any]) -> str:
        """Generate section debug information"""
        if not error_data.get('debug_info'):
            return ""
        
        debug_info = error_data['debug_info']
        
        debug_html = '''
        <div class="debug-section">
            <div class="debug-header" onclick="toggleDebug()">
                <h3>Informasi Debug</h3>
                <span class="debug-toggle">▼</span>
            </div>
            <div class="debug-content" id="debugContent">
        '''
        
        # Python version
        if 'python_version' in debug_info:
            debug_html += f'<div class="debug-item"><strong>Versi Python:</strong> <code>{html.escape(debug_info["python_version"])}</code></div>'
        
        # Traceback
        if 'traceback' in debug_info:
            traceback_html = html.escape(debug_info['traceback'])
            debug_html += f'''
            <div class="debug-item">
                <strong>Traceback:</strong>
                <pre class="traceback"><code>{traceback_html}</code></pre>
            </div>
            '''
        
        # Request data
        if error_data.get('request_data'):
            request_html = html.escape(json.dumps(error_data['request_data'], indent=2))
            debug_html += f'''
            <div class="debug-item">
                <strong>Data Request:</strong>
                <pre class="request-data"><code>{request_html}</code></pre>
            </div>
            '''
        
        debug_html += '''
            </div>
        </div>
        '''
        
        return debug_html
    
    def _get_modern_error_css(self) -> str:
        """Get CSS styles modern untuk halaman error"""
        return '''
        * {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', sans-serif;
  background: linear-gradient(to bottom right, #dfe9f3, #ffffff);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  line-height: 1.6;
  color: #333;
}

.error-container {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.05);
  max-width: 800px;
  width: 100%;
  overflow: hidden;
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-content {
  padding: 40px;
}

.error-header {
  text-align: center;
  margin-bottom: 24px;
}

.error-icon svg {
  width: 70px;
  height: 70px;
  color: #e3342f;
  margin-bottom: 16px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.error-code {
  font-size: 3rem;
  font-weight: bold;
  color: #e3342f;
}

.error-title {
  font-size: 1.5rem;
  color: #444;
  font-weight: 500;
}

.error-description {
  text-align: center;
  font-size: 1rem;
  margin: 20px 0;
  color: #666;
}

.messages-error {
  text-align: justify;
  font-size: 0.95rem;
  color: #555;
  background: #fdfdfd;
  border-left: 4px solid #ffc107;
  padding: 15px 20px;
  border-radius: 6px;
  margin: 16px 0;
}

.danger-info {
  background: #fef1f1;
  border-left: 4px solid #e3342f;
  padding: 12px 18px;
  border-radius: 6px;
  color: #991b1b;
  font-size: 0.95rem;
  margin-top: 20px;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 30px;
}

.btn {
  text-align: center;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s ease;
}

.btn-primary {
  background: #3490dc;
  color: #fff;
}

.btn-primary:hover {
  background: #2779bd;
}

.btn-secondary {
  background: #6c757d;
  color: #fff;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-outline {
  background: transparent;
  color: #3490dc;
  border: 2px solid #3490dc;
}

.btn-outline:hover {
  background: #3490dc;
  color: #fff;
}

pre, .traceback, .request-data {
  background: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  overflow-x: auto;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .error-code {
    font-size: 2.5rem;
  }

  .error-title {
    font-size: 1.2rem;
  }

  .error-content {
    padding: 24px;
  }

  .btn {
    width: 100%;
    max-width: 240px;
  }
  .btn-outline{
    padding: 5px 10px;
  }
}
        '''
    
    def _get_error_page_js(self) -> str:
        """Get JavaScript untuk interaktivitas halaman error"""
        return '''
        function toggleDebug() {
            const content = document.getElementById('debugContent');
            const toggle = document.querySelector('.debug-toggle');
            
            if (content.classList.contains('show')) {
                content.classList.remove('show');
                toggle.classList.remove('rotated');
            } else {
                content.classList.add('show');
                toggle.classList.add('rotated');
            }
        }
        
        // Auto-hide debug section after 30 seconds
        setTimeout(function() {
            const content = document.getElementById('debugContent');
            const toggle = document.querySelector('.debug-toggle');
            if (content && content.classList.contains('show')) {
                content.classList.remove('show');
                toggle.classList.remove('rotated');
            }
        }, 30000);
        
        // Smooth scroll untuk long content
        document.addEventListener('DOMContentLoaded', function() {
            const traceback = document.querySelector('.traceback');
            if (traceback && traceback.scrollHeight > traceback.clientHeight) {
                traceback.style.cursor = 'grab';
            }
        });
        '''
    
    def _sanitize_for_html(self, data: Any) -> Any:
        """Recursively sanitize data untuk HTML output"""
        if isinstance(data, dict):
            return {key: self._sanitize_for_html(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_html(item) for item in data]
        elif isinstance(data, str):
            return html.escape(data)
        else:
            return data
    
    def _get_fallback_error_response(self) -> Dict[str, Any]:
        """Get minimal fallback error response ketika semua gagal"""
        fallback_html = '''
        <!DOCTYPE html>
        <html lang="id">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>500 Internal Server Error</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .error { color: #dc3545; }
                </style>
            </head>
            <body>
                <h1 class="error">500 Internal Server Error</h1>
                <p>An unexpected error occurred in the error handler.</p>
                <button onclick="history.back()">Back</button>
            </body>
        </html>
        '''.strip()
        
        return {
            'status_code': 500,
            'content_type': 'text/html',
            'body': fallback_html,
            'headers': {'X-Error-Type': 'Fallback'}
        }
    
    def create_json_error_response(self, error: Union[Exception, int], 
                                 request_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Create JSON error response untuk API endpoints"""
        error_data = self.handle_error(error, request_data)
        
        json_response = {
            'error': True,
            'status_code': error_data['status_code'],
            'message': self.status_messages.get(error_data['status_code'], 'Unknown Error'),
            'timestamp': datetime.now().isoformat()
        }
        
        if isinstance(error, Exception):
            json_response['exception_type'] = type(error).__name__
            if self.debug:
                json_response['exception_message'] = str(error)
                json_response['traceback'] = traceback.format_exc()
        
        return {
            'status_code': error_data['status_code'],
            'content_type': 'application/json',
            'body': json.dumps(json_response, indent=2 if self.debug else None),
            'headers': {'X-Error-Type': 'JSON'}
        }


# Custom exception classes untuk better error handling
class HTTPException(Exception):
    """Base HTTP exception with status code"""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
        self. message = message


class BadRequest(HTTPException):
    def __init__(self, message: str = "Invalid Request"):
        super().__init__(message, 400)


class Unauthorized(HTTPException):
    def __init__(self, message: str = "Not Authorized"):
        super().__init__(message, 401)


class Forbidden(HTTPException):
    def __init__(self, message: str = "Access Denied"):
        super().__init__(message, 403)


class NotFound(HTTPException):
    def __init__(self, message: str = "Not Found"):
        super().__init__(message, 404)


class MethodNotAllowed(HTTPException):
    def __init__(self, message: str = "Method Not Allowed"):
        super().__init__(message, 405)


class InternalServerError(HTTPException):
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(message, 500)


class HTTPExceptions(Exception):
    def __init__(self, message: str = "", status_code: int = 500, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self. message = message
        self. body = body


# Enhanced PieShark Framework Integration
class PieSharkErrorMixin:
    """A mixin to add error handling capabilities to the PieShark framework"""
    
    def __init__(self, *args, **kwargs):
        self.error_handler = ErrorHandler(
            debug=getattr(self, 'debug', False),
            app_name=getattr(self, 'name', 'PieShark App')
        )
    
    def register_error_handler(self, status_code: int):
        """Decorator to register error handlers for certain status codes"""
        def decorator(func):
            self.error_handler.register_error_handler(status_code, func)
            return func
        return decorator
    
    def register_exception_handler(self, exception_type: type):
        """Decorator to register an exception handler for a specific exception type"""
        def decorator(func):
            self.error_handler.register_exception_handler(exception_type, func)
            return func
        return decorator
    
    def _handle_request_error(self, error: Union[Exception, int], request_data: Dict = None):
        """Internal method to handle request errors"""
        # Get request data from current request context if not provided
        if request_data is None:
            request_data = self._get_current_request_data()
        
        # Check if the client wants a JSON response (API endpoint)
        accept_header = request_data.get('headers', {}).get('Accept', '')
        if 'application/json' in accept_header:
            return self.error_handler.create_json_error_response(error, request_data)
        else:
            return self.error_handler.handle_error(error, request_data)
    
    def _get_current_request_data(self) -> Dict:
        """Extract current request data - implementation based on framework structure"""
        # Implementation based on how the PieShark framework handles requests
        return {
            'method': getattr(self, 'method', 'GET'),
            'path': getattr(self, 'path', '/'),
            'headers': getattr(self, 'headers', {}),
            'query_params': getattr(self, 'query_params', {}),
            'remote_addr': getattr(self, 'remote_addr', '127.0.0.1')
        }
    
    def abort(self, status_code=404, description=None):
        request_data = getattr(self, 'environ', {})
        
        # Create an HTTPException with the given description
        error = HTTPException(description, status_code)
        
        # Add custom_description to request_data so it can be accessed later
        if request_data is None:
            request_data = {}
        request_data['custom_description'] = description
        
        error_response = self._handle_request_error(error, request_data)
        
        # Fix typo: response -> response
        response = Response(
            body=error_response.get("body", "Aborted"),
            status=error_response.get("status_code", 500),
            content_type=error_response.get("content_type", "text/html"),
            headers=error_response.get("headers", {})
        )
        response.status_code = status_code
        response.content_type = error_response.get("content_type", "text/html")
        return response

# Utility functions untuk error handling
def create_error_handler(debug=False, app_name="PieShark App"):
    """Factory function untuk membuat ErrorHandler instance"""
    return ErrorHandler(debug=debug, app_name=app_name)


def handle_404(request_data=None):
    """Quick function untuk handle 404 errors"""
    handler = ErrorHandler()
    return handler.handle_error(404, request_data)


def handle_500(exception, request_data=None):
    """Quick function untuk handle 500 errors"""
    handler = ErrorHandler()
    return handler.handle_error(exception, request_data)


# Decorator untuk auto error handling
def error_handler_decorator(handler_instance=None):
    """Decorator untuk automatic error handling pada functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if handler_instance:
                    return handler_instance.handle_error(e)
                else:
                    # Fallback handler
                    fallback_handler = ErrorHandler()
                    return fallback_handler.handle_error(e)
        return wrapper
    return decorator


# Context manager untuk error handling
class ErrorContext:
    """Context manager untuk handle errors dalam blok kode"""
    
    def __init__(self, handler: ErrorHandler = None, reraise: bool = False):
        self.handler = handler or ErrorHandler()
        self.reraise = reraise
        self.error_response = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_response = self.handler.handle_error(exc_val)
            if not self.reraise:
                # Suppress exception jika reraise=False
                return True
        return False


# Advanced error logging
class ErrorLogger:
    """Enhanced error logger dengan berbagai output formats"""
    
    def __init__(self, log_file: str = None, log_level: int = logging.ERROR):
        self.logger = logging.getLogger("pieshark_errors")
        self.logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler jika disediakan
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_error(self, error: Exception, request_data: Dict = None, extra_info: Dict = None):
        """Log error dengan informasi lengkap"""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        
        if request_data:
            error_info['request_data'] = request_data
        
        if extra_info:
            error_info['extra_info'] = extra_info
        
        self.logger.error(json.dumps(error_info, indent=2))
    
    def log_http_error(self, status_code: int, request_data: Dict = None):
        """Log HTTP error"""
        error_info = {
            'error_type': 'HTTP_ERROR',
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        
        if request_data:
            error_info['request_data'] = request_data
        
        self.logger.error(json.dumps(error_info, indent=2))


# Example usage dan testing
if __name__ == "__main__":
    # Test basic error handler
    handler = ErrorHandler(debug=True, app_name="Test App")
    
    # Test 404 error
    print("=== Testing 404 Error ===")
    response_404 = handler.handle_error(404)
    print(f"Status: {response_404['status_code']}")
    print(f"Content Type: {response_404['content_type']}")
    
    # Test exception
    print("\n=== Testing Exception ===")
    try:
        raise ValueError("Test exception")
    except Exception as e:
        response_exc = handler.handle_error(e)
        print(f"Status: {response_exc['status_code']}")
        print(f"Content Type: {response_exc['content_type']}")
    
    # Test custom error handler
    print("\n=== Testing Custom Handler ===")
    def custom_404_handler(status_code, request_data):
        return {
            'status_code': status_code,
            'content_type': 'text/plain',
            'body': 'Custom 404 Handler Response',
            'headers': {}
        }
    
    handler.register_error_handler(404, custom_404_handler)
    custom_response = handler.handle_error(404)
    print(f"Custom Response: {custom_response['body']}")
    
    # Test JSON response
    print("\n=== Testing JSON Response ===")
    json_response = handler.create_json_error_response(500)
    print(f"JSON Status: {json_response['status_code']}")
    print(f"JSON Body: {json_response['body']}")
    
    print("\n=== Error Handler Testing Complete ===")


# Export utama
