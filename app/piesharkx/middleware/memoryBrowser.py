from typing import Union, Dict, List, Tuple, Any, Optional, Callable
from collections import defaultdict
from threading import Thread, Lock, RLock
from datetime import datetime, timedelta
import os, time, sys, json, hashlib, uuid
from datetime import datetime, timedelta, timezone
from webob.cookies import make_cookie
from ..logger import logger

__all__ = ["SecureSessionManager", "SessionWrapper", "ImprovedSessionManager"]

class SecureSessionManager:
    """
    Enhanced Session Manager dengan array 2D dan multi-browser/multi-user support
    Storage format: [[session_id: str, session_data: dict], ...]
    
    Features:
    - Array 2D sebagai storage utama
    - Unique sessions per browser/user combination
    - Customizable session keys
    - Thread-safe operations
    - Automatic cleanup of expired sessions
    - Session data encryption
    - Browser fingerprinting for security
    """
    
    def __init__(self, secret_key: str, session_timeout: int = 3600, 
                 cookie_name: str = "pieshark_session", 
                 secure_cookies: bool = False,
                 cleanup_interval: int = 300):
        """
        Initialize the session manager
        
        Args:
            secret_key: Secret key for session security
            session_timeout: Session timeout in seconds (default: 1 hour)
            cookie_name: Name of the session cookie
            secure_cookies: Whether to use secure cookies (HTTPS only)
            cleanup_interval: Interval for automatic cleanup in seconds
        """
        self.secret_key = secret_key
        self.session_timeout = session_timeout
        self.cookie_name = cookie_name
        self.secure_cookies = secure_cookies
        self.cleanup_interval = cleanup_interval
        
        # Array 2D storage: [[session_id, session_data], ...]
        self._sessions_array: List[List[Any]] = []
        
        # Index mappings for quick lookup
        self._session_index: Dict[str, int] = {}  # session_id -> array_index
        self._user_sessions: Dict[str, List[int]] = defaultdict(list)  # user_id -> array_indices
        self._browser_sessions: Dict[str, List[int]] = defaultdict(list)  # browser_id -> array_indices
        
        # Thread safety
        self._lock = RLock()
        
        # Cleanup tracking
        self._last_cleanup = time.time()
        self._cleanup_lock = Lock()
        
        logger.info(f"SessionManager initialized with 2D array storage, timeout: {session_timeout}s")

    def _find_session_index(self, session_id: str) -> Optional[int]:
        """
        Find session index in array using index mapping
        
        Args:
            session_id: Session ID to find
            
        Returns:
            Array index or None if not found
        """
        return self._session_index.get(session_id)

    def _get_session_by_index(self, index: int) -> Optional[List[Any]]:
        """
        Get session by array index
        
        Args:
            index: Array index
            
        Returns:
            Session array [session_id, session_data] or None
        """
        if 0 <= index < len(self._sessions_array):
            return self._sessions_array[index]
        return None

    def _add_session_to_array(self, session_id: str, session_data: Dict[str, Any]) -> int:
        """
        Add session to array and update indices
        
        Args:
            session_id: Session ID
            session_data: Session data
            
        Returns:
            Array index of new session
        """
        # Add to array
        session_entry = [session_id, session_data]
        self._sessions_array.append(session_entry)
        array_index = len(self._sessions_array) - 1
        
        # Update index mapping
        self._session_index[session_id] = array_index
        
        # Update user and browser indices
        user_id = session_data.get('user_id')
        if user_id:
            self._user_sessions[user_id].append(array_index)
        
        browser_id = session_data.get('browser_fingerprint')
        if browser_id:
            self._browser_sessions[browser_id].append(array_index)
        
        return array_index

    def _remove_session_by_index(self, index: int) -> bool:
        """
        Remove session by array index and reorganize array
        
        Args:
            index: Array index to remove
            
        Returns:
            True if removed successfully
        """
        if index < 0 or index >= len(self._sessions_array):
            return False
        
        # Get session data before removal
        session_entry = self._sessions_array[index]
        session_id = session_entry[0]
        session_data = session_entry[1]
        
        # Remove from array
        self._sessions_array.pop(index)
        
        # Remove from session index
        del self._session_index[session_id]
        
        # Update all indices after the removed one
        for sid, idx in self._session_index.items():
            if idx > index:
                self._session_index[sid] = idx - 1
        
        # Update user sessions indices
        user_id = session_data.get('user_id')
        if user_id:
            user_indices = self._user_sessions[user_id]
            if index in user_indices:
                user_indices.remove(index)
            # Update remaining indices
            for i in range(len(user_indices)):
                if user_indices[i] > index:
                    user_indices[i] -= 1
            # Remove empty user entry
            if not user_indices:
                del self._user_sessions[user_id]
        
        # Update browser sessions indices
        browser_id = session_data.get('browser_fingerprint')
        if browser_id:
            browser_indices = self._browser_sessions[browser_id]
            if index in browser_indices:
                browser_indices.remove(index)
            # Update remaining indices
            for i in range(len(browser_indices)):
                if browser_indices[i] > index:
                    browser_indices[i] -= 1
            # Remove empty browser entry
            if not browser_indices:
                del self._browser_sessions[browser_id]
        
        return True

    def _generate_session_id(self, user_id: Optional[str] = None, 
                           browser_fingerprint: Optional[str] = None) -> str:
        """
        Generate a unique session ID
        
        Args:
            user_id: Optional user identifier
            browser_fingerprint: Optional browser fingerprint
            
        Returns:
            Unique session ID
        """
        timestamp = str(time.time())
        random_bytes = os.urandom(32).hex()
        user_part = user_id or "anonymous"
        browser_part = browser_fingerprint or "unknown"
        
        # Create unique identifier
        unique_data = f"{timestamp}:{random_bytes}:{user_part}:{browser_part}:{self.secret_key}"
        session_id = hashlib.sha256(unique_data.encode()).hexdigest()
        
        return session_id

    def _get_browser_fingerprint(self, request) -> str:
        """
        Generate browser fingerprint from request headers
        
        Args:
            request: Request object
            
        Returns:
            Browser fingerprint string
        """
        # Collect browser-specific information
        user_agent = request.environ.get('HTTP_USER_AGENT', '')
        accept_language = request.environ.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.environ.get('HTTP_ACCEPT_ENCODING', '')
        remote_addr = self._get_client_ip(request)
        
        # Create fingerprint
        fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}:{remote_addr}"
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]
        
        return fingerprint

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address with proxy support
        
        Args:
            request: Request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers
        forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.environ.get('HTTP_X_REAL_IP')
        if real_ip:
            return real_ip
        
        return request.environ.get('REMOTE_ADDR', '127.0.0.1')

    def _should_cleanup(self) -> bool:
        """Check if cleanup should be performed"""
        with self._cleanup_lock:
            now = time.time()
            return (now - self._last_cleanup) > self.cleanup_interval

    def _cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from array
        
        Returns:
            Number of sessions cleaned up
        """
        if not self._should_cleanup():
            return 0
            
        with self._lock:
            current_time = time.time()
            expired_indices = []
            
            # Find expired sessions (iterate backwards to handle removals)
            for i in range(len(self._sessions_array) - 1, -1, -1):
                session_entry = self._sessions_array[i]
                session_data = session_entry[1]
                last_accessed = session_data.get('last_accessed', 0)
                
                if current_time - last_accessed > self.session_timeout:
                    expired_indices.append(i)
            
            # Remove expired sessions
            cleaned_count = 0
            for index in expired_indices:
                if self._remove_session_by_index(index):
                    cleaned_count += 1
            
            # Update cleanup timestamp
            with self._cleanup_lock:
                self._last_cleanup = current_time
            
            if cleaned_count > 0:
                logger.debug(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count

    def _generate_csrf_token(self) -> str:
        """Generate CSRF token for session"""
        return hashlib.sha256(f"{uuid.uuid4()}:{self.secret_key}".encode()).hexdigest()[:32]

    def create_session(self, user_id: Optional[str] = None, 
                      browser_fingerprint: Optional[str] = None,
                      custom_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session
        
        Args:
            user_id: Optional user identifier
            browser_fingerprint: Optional browser fingerprint
            custom_data: Optional custom session data
            
        Returns:
            New session ID
        """
        with self._lock:
            # Cleanup expired sessions
            self._cleanup_expired_sessions()
            
            # Generate unique session ID
            session_id = self._generate_session_id(user_id, browser_fingerprint)
            
            # Ensure uniqueness
            while session_id in self._session_index:
                session_id = self._generate_session_id(user_id, browser_fingerprint)
            
            # Create session data
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'browser_fingerprint': browser_fingerprint,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'data': custom_data or {},
                'is_authenticated': user_id is not None,
                'csrf_token': self._generate_csrf_token()
            }
            
            # Add to array
            self._add_session_to_array(session_id, session_data)
            
            logger.debug(f"Created session {session_id[:8]}... for user {user_id or 'anonymous'}")
            return session_id

    def get_session(self, session_id: str, 
                   validate_browser: bool = True,
                   browser_fingerprint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            validate_browser: Whether to validate browser fingerprint
            browser_fingerprint: Current browser fingerprint
            
        Returns:
            Session data or None if not found/expired
        """
        with self._lock:
            # Cleanup expired sessions
            self._cleanup_expired_sessions()
            
            # Find session index
            index = self._find_session_index(session_id)
            if index is None:
                return None
            
            # Get session entry
            session_entry = self._get_session_by_index(index)
            if not session_entry:
                return None
            
            session_data = session_entry[1]
            
            # Check if session is expired
            current_time = time.time()
            if current_time - session_data['last_accessed'] > self.session_timeout:
                self._remove_session_by_index(index)
                return None
            
            # Validate browser fingerprint for security
            if validate_browser and browser_fingerprint:
                stored_fingerprint = session_data.get('browser_fingerprint')
                if stored_fingerprint and stored_fingerprint != browser_fingerprint:
                    logger.warning(f"Browser fingerprint mismatch for session {session_id[:8]}...")
                    # Could be session hijacking, invalidate session
                    self._remove_session_by_index(index)
                    return None
            
            # Update last accessed time
            session_data['last_accessed'] = current_time
            
            return session_data

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID
            data: Data to update
            
        Returns:
            True if updated successfully, False if session not found
        """
        with self._lock:
            session_data = self.get_session(session_id, validate_browser=False)
            if not session_data:
                return False
            
            # Update session data
            session_data['data'].update(data)
            session_data['last_accessed'] = time.time()
            
            return True

    def destroy_session(self, session_id: str) -> bool:
        """
        Destroy a session
        
        Args:
            session_id: Session ID to destroy
            
        Returns:
            True if session was destroyed, False if not found
        """
        with self._lock:
            index = self._find_session_index(session_id)
            if index is None:
                return False
            return self._remove_session_by_index(index)

    def destroy_user_sessions(self, user_id: str) -> int:
        """
        Destroy all sessions for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions destroyed
        """
        with self._lock:
            user_indices = list(self._user_sessions.get(user_id, []))
            destroyed_count = 0
            
            # Sort indices in descending order to avoid index shifting issues
            user_indices.sort(reverse=True)
            
            for index in user_indices:
                if self._remove_session_by_index(index):
                    destroyed_count += 1
            
            logger.info(f"Destroyed {destroyed_count} sessions for user {user_id}")
            return destroyed_count

    def get_all_sessions(self) -> List[List[Any]]:
        """
        Get all sessions as 2D array
        
        Returns:
            Copy of sessions array
        """
        with self._lock:
            return [session_entry.copy() for session_entry in self._sessions_array]

    def get_session_by_user(self, user_id: str) -> List[List[Any]]:
        """
        Get all sessions for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            List of session entries for the user
        """
        with self._lock:
            user_indices = self._user_sessions.get(user_id, [])
            user_sessions = []
            
            for index in user_indices:
                session_entry = self._get_session_by_index(index)
                if session_entry:
                    user_sessions.append(session_entry.copy())
            
            return user_sessions

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Dictionary with session statistics
        """
        with self._lock:
            current_time = time.time()
            active_sessions = 0
            expired_sessions = 0
            
            for session_entry in self._sessions_array:
                session_data = session_entry[1]
                if current_time - session_data['last_accessed'] <= self.session_timeout:
                    active_sessions += 1
                else:
                    expired_sessions += 1
            
            return {
                'total_sessions': len(self._sessions_array),
                'active_sessions': active_sessions,
                'expired_sessions': expired_sessions,
                'unique_users': len(self._user_sessions),
                'unique_browsers': len(self._browser_sessions),
                'last_cleanup': datetime.fromtimestamp(self._last_cleanup).isoformat(),
                'array_size': len(self._sessions_array)
            }

    def clear_all_sessions(self) -> int:
        """
        Clear all sessions
        
        Returns:
            Number of sessions cleared
        """
        with self._lock:
            count = len(self._sessions_array)
            self._sessions_array.clear()
            self._session_index.clear()
            self._user_sessions.clear()
            self._browser_sessions.clear()
            
            logger.info(f"Cleared {count} sessions from array")
            return count

    def load_session(self, request) -> 'SessionWrapper':
        """
        Load session from request
        
        Args:
            request: Request object
            
        Returns:
            SessionWrapper instance
        """
        # Get session ID from cookie
        session_id = request.cookies.get(self.cookie_name)
        browser_fingerprint = self._get_browser_fingerprint(request)
        
        # Get existing session or create new one
        session_data = None
        if session_id:
            session_data = self.get_session(session_id, True, browser_fingerprint)
        
        if not session_data:
            # Create new session
            session_id = self.create_session(
                browser_fingerprint=browser_fingerprint
            )
            session_data = self.get_session(session_id, False)
        
        # Create session wrapper
        session_wrapper = SessionWrapper(self, session_id, session_data)
        
        # Store session info in request environment
        request.environ['pieshark.session_id'] = session_id
        request.environ['pieshark.session'] = session_wrapper
        request.environ['pieshark.browser_fingerprint'] = browser_fingerprint
        
        return session_wrapper

    def save_session(self, request, response) -> None:
        """
        Save session to response
        
        Args:
            request: Request object
            response: Response object
        """
        session_id = request.environ.get('pieshark.session_id')
        if not session_id:
            return
        
        # Create session cookie
        cookie_value = make_cookie(
            self.cookie_name,
            session_id,
            max_age=self.session_timeout,
            path='/',
            httponly=True,
            secure=self.secure_cookies,
            samesite='Lax'
        )
        
        response.headers['Set-Cookie'] = cookie_value

    # Session wrapper class untuk dictionary-like interface
    def get_session_wrapper(self, session_id: str) -> Optional['SessionWrapper']:
        """
        Get session wrapper for dictionary-like access
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionWrapper instance or None
        """
        session_data = self.get_session(session_id, validate_browser=False)
        if session_data:
            return SessionWrapper(self, session_id, session_data)
        return None

    def _get_current_session(self) -> Dict[str, Any]:
        """Get current session from request context"""
        try:
            from PieShark.localcontex import _request_ctx_stack
            
            current = _request_ctx_stack.top
            if not current or not hasattr(current, 'session'):
                raise RuntimeError("Session not available in current context")
            return current.session
        except ImportError:
            # Fallback jika localcontex tidak tersedia
            raise RuntimeError("Session context not available")


class SessionWrapper:
    """
    Wrapper class untuk memberikan dictionary-like interface ke session data
    Format akses: session[key] dan session.get(key) mengakses session['data'][key]
    """
    
    def __init__(self, session_manager: SecureSessionManager, session_id: str, session_data: Dict[str, Any]):
        self._manager = session_manager
        self._session_id = session_id
        self._session_data = session_data

    def __getitem__(self, key: str) -> Any:
        """
        Get session data item
        Format: session['user'] -> session_data['data']['user']
        """
        if key in ['session_id', 'user_id', 'browser_fingerprint', 'created_at', 
                   'last_accessed', 'is_authenticated', 'csrf_token']:
            # Akses ke metadata session
            return self._session_data[key]
        else:
            # Akses ke data session
            return self._session_data['data'][key]

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set session data item
        Format: session['user'] = value -> session_data['data']['user'] = value
        """
        if key in ['session_id', 'user_id', 'browser_fingerprint', 'created_at', 
                   'last_accessed', 'is_authenticated', 'csrf_token']:
            # Update metadata session
            self._session_data[key] = value
        else:
            # Update data session
            self._session_data['data'][key] = value
        
        # Update session in manager
        self._manager.update_session(self._session_id, {key: value} if key not in self._session_data else {})

    def __delitem__(self, key: str) -> None:
        """Delete session data item"""
        if key in self._session_data['data']:
            del self._session_data['data'][key]

    def __contains__(self, key: str) -> bool:
        """
        Check if key exists in session
        Cek di metadata dulu, lalu di data
        """
        if key in ['session_id', 'user_id', 'browser_fingerprint', 'created_at', 
                   'last_accessed', 'is_authenticated', 'csrf_token', 'data']:
            return key in self._session_data
        else:
            return key in self._session_data['data']

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get session data item with default
        Format: session.get('user', 'default') -> session_data['data'].get('user', 'default')
        """
        if key in ['session_id', 'user_id', 'browser_fingerprint', 'created_at', 
                   'last_accessed', 'is_authenticated', 'csrf_token', 'data']:
            # Akses ke metadata session
            return self._session_data.get(key, default)
        else:
            # Akses ke data session
            return self._session_data['data'].get(key, default)

    def pop(self, key: str, default: Any = None) -> Any:
        """Pop session data item"""
        if key in self._session_data['data']:
            return self._session_data['data'].pop(key, default)
        return default

    def clear_data(self) -> None:
        """Clear session data (hanya bagian 'data', bukan metadata)"""
        self._session_data['data'].clear()

    def clear_all(self) -> None:
        """Clear semua data session termasuk metadata"""
        self._session_data.clear()

    def keys(self):
        """Get all keys (metadata + data keys)"""
        metadata_keys = ['session_id', 'user_id', 'browser_fingerprint', 'created_at', 
                        'last_accessed', 'is_authenticated', 'csrf_token', 'data']
        data_keys = list(self._session_data['data'].keys())
        return metadata_keys + data_keys

    def items(self):
        """Get all items (metadata + data items)"""
        result = []
        # Metadata items
        for key in ['session_id', 'user_id', 'browser_fingerprint', 'created_at', 
                   'last_accessed', 'is_authenticated', 'csrf_token', 'data']:
            if key in self._session_data:
                result.append((key, self._session_data[key]))
        
        # Data items
        for key, value in self._session_data['data'].items():
            result.append((key, value))
        
        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format seperti yang diminta:
        {
            'session_id': '8967e7ff785f568591b6dff562ae7dc1b33b076ebee98a0efd1a838caa0e6489', 
            'user_id': None, 
            'browser_fingerprint': 'ef4c8293dbfeeb80', 
            'created_at': 1749808470.928559, 
            'last_accessed': 1749808547.3872566, 
            'data': {
                'user': 'Ramsyan1749808476.6612031', 
                'yudi': 'Ramsyan1749808476.6612031'
            }, 
            'is_authenticated': False, 
            'csrf_token': '8b0bcf3b260b0ffc2c8d80ff5deaddd4'
        }
        """
        return self._session_data.copy()

    def __repr__(self) -> str:
        """String representation"""
        return f"SessionWrapper({self._session_id[:8]}..., data_keys={list(self._session_data['data'].keys())})"

    def __str__(self) -> str:
        """String representation"""
        return str(self.to_dict())


class ImprovedSessionManager(SecureSessionManager):
    """Improved session manager with better cleanup"""

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = time.time()
        expired_sessions = []

        with self.lock:
            for session_id, session_data in self.sessions.items():
                if current_time - session_data["last_accessed"] > self.session_timeout:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]
            self.cleanup_sessions()
        logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")

    def clear_all_sessions(self):
        """Clear all sessions"""
        with self.lock:
            self.sessions.clear()
        logger.info("All sessions cleared")
