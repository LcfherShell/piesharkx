from .date_moduler import datetime, datetime_next, datetime_now, datetime_UTF, UTC_DATE_TIME, TimeStamp
from .handler import OrderedDict, SelectType, create_secure_memory
from .handler.endecryptions import AESCipher, AESCipher_2
from os import environ as env
from hashlib import md5

__all__ = ["CookieManajer", "Cookie"]

class CookieValue:
    """
    Wrapper class untuk nilai cookie yang memungkinkan akses ke encrypted value dan decode method
    """
    def __init__(self, key, encrypted_value, aes_cipher):
        self.key = key
        self.encrypted_value = encrypted_value
        self.aes_cipher = aes_cipher
        self._original_value = None
    
    def __str__(self):
        return self.encrypted_value
    
    def __repr__(self):
        return f"CookieValue(key='{self.key}', encrypted='{self.encrypted_value}')"
    
    def decode(self):
        """
        Decode encrypted cookie value back to original value
        """
        try:
            # Remove quotes if present
            clean_value = self.encrypted_value.replace("'", "").replace('"', '')
            decoded_bytes = self.aes_cipher.decrypt(clean_value)
            if isinstance(decoded_bytes, bytes):
                return decoded_bytes.decode('utf-8')
            return str(decoded_bytes)
        except Exception as e:
            return f"Error decoding V1: {str(e)}"

class CookieSelector:
    """
    Struct-like object untuk mengakses cookie values dengan dot notation
    """
    def __init__(self, cookie_instance):
        self._cookie_instance = cookie_instance
        self._cookies = {}
    
    def __getattr__(self, name):
        if name in self._cookies:
            return self._cookies[name]
        raise AttributeError(f"Cookie '{name}' not found")
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._cookies[name] = value
    
    def __contains__(self, key):
        return key in self._cookies
    
    def __iter__(self):
        return iter(self._cookies)
    
    def keys(self):
        return self._cookies.keys()
    
    def values(self):
        return self._cookies.values()
    
    def items(self):
        return self._cookies.items()
    
    def get(self, key, default=None):
        return self._cookies.get(key, default)

class CookieManajer:
    def __init__(self, aes, __cookie_secure):
        self.aes = aes
        self.__cookie_secure = __cookie_secure

    def __call__(self, value: str):
        return self.enc(value)
    
    def __str__(self):
        return self.__cookie_secure
    
    def __repr__(self):
        return self.__cookie_secure

    def enc(self, value):
        """
        Encrypt a value using AES cipher
        """
        try:
            # Convert value to string if it's not already
            if isinstance(value, str):
                string_value = value
            elif isinstance(value, bytes):
                string_value = value.decode('utf-8')
            else:
                string_value = str(value)
            
            # Encrypt the string value
            encrypted_result = self.aes.encrypt(string_value)
            
            # Handle different return types from AES encryption
            if isinstance(encrypted_result, bytes):
                return encrypted_result.decode('utf-8')
            elif isinstance(encrypted_result, str):
                return encrypted_result
            else:
                return str(encrypted_result)
        except Exception as e:
            return f"Error encrypting: {str(e)}"

    def decode(self, encrypted_value):
        """
        Decode an encrypted value
        """
        try:
            # Remove quotes if present
            clean_value = encrypted_value.replace("'", "").replace('"', '')
            decrypted_bytes = self.aes.decrypt(clean_value)
            if isinstance(decrypted_bytes, bytes):
                return decrypted_bytes.decode('utf-8')
            return str(decrypted_bytes)
        except Exception as e:
            return f"Error decoding V2: {str(e)}"

class Cookie:
    def __init__(self, salt, exp=1, app=None):
        super(Cookie, self).__init__()
        if app:
            environ: SelectType.Dict_ = dict(app.__dict__)
        else:
            environ: SelectType.Dict_ = dict(env)
        self.exp = exp
        self.__cookie_secure = None
        self.aes = Cookie._Cookie__encreet(secure=True, salt=salt, environs=environ)
        self.cookie = CookieManajer(self.aes, self.__cookie_secure)
        
        # Initialize the selector for struct-like access
        self.select = CookieSelector(self)
        
        # Store created cookies
        self._created_cookies = {}

    def __call__(self, response):
        response.headers['Set-Cookie'] = self.__cookie_secure

    def __str__(self):
        return str(self.__cookie_secure)
    
    def __repr__(self):
        return f"Cookie(exp={self.exp}, cookies={list(self.select.keys())})"
    
    def __paired__(self, **kwargs):
        return tuple(kwargs)
    
    def create(self, cookie_string):
        """
        Create encrypted cookie from string like 'key=value'
        
        Args:
            cookie_string: String in format 'key=value' or dict with key-value pairs
        
        Returns:
            Cookie instance for chaining
        """
        if isinstance(cookie_string, str):
            # Parse single cookie string
            if '=' in cookie_string:
                key, value = cookie_string.split('=', 1)
                self._create_single_cookie(key.strip(), value.strip())
            else:
                raise ValueError("Cookie string must be in format 'key=value'")
        
        elif isinstance(cookie_string, dict):
            # Handle dictionary input
            for key, value in cookie_string.items():
                self._create_single_cookie(str(key), str(value))
        
        else:
            raise ValueError("Cookie input must be string in format 'key=value' or dictionary")
        
        return self
    
    def _create_single_cookie(self, key, value):
        """
        Create a single encrypted cookie
        """
        # Encrypt the value
        encrypted_value = self.cookie.enc(value)
        
        # Create CookieValue object
        cookie_value = CookieValue(key, encrypted_value, self.aes)
        
        # Store in selector for dot notation access
        setattr(self.select, key, cookie_value)
        
        # Store in internal dict
        self._created_cookies[key] = cookie_value
        
        # Update the cookie secure string
        cookie_pair = f"{key}='{encrypted_value}'"
        if self.__cookie_secure:
            self.__cookie_secure += f"; {cookie_pair}"
        else:
            self.__cookie_secure = cookie_pair
    
    def create_multiple(self, **kwargs):
        """
        Create multiple cookies at once
        
        Usage:
            cookie.create_multiple(data="value1", user="value2", token="value3")
        """
        for key, value in kwargs.items():
            self._create_single_cookie(key, str(value))
        return self
    
    def get_cookie(self, key):
        """
        Get cookie by key
        """
        return self.select.get(key)
    
    def get_all_cookies(self):
        """
        Get all created cookies
        """
        return dict(self.select.items())
    
    def base(self, request):
        cookie = self.__cookie_secure
        try:
            cookies = (dict(i.split('=', 1) for i in cookie.split('; ')))
        except:
            cookies = request.cookies
        return cookies

    @classmethod
    def __encreet(cls, secure, salt, environs):
        if secure and environs.get('secret_key'):
            #assert len(str(environs.get('secret_key'))) >= 3 and len(str(environs.get('secret_key'))) <= 14
            if salt and len(salt) >= 23 and len(salt) <= 34:
                return AESCipher_2(secretKey=environs.get('secret_key').strip(), salt=salt)
            else:
                return AESCipher(key=environs.get('secret_key').strip())

    def __enc(self, path):
        get_dir = dir(self)
        self.__cookie_secure = path
        if 'aes' in get_dir:
            split_get_key = str(path).split('=')
            get_key_head_cookie = split_get_key[0]
            self.path = path.replace(get_key_head_cookie, '')
            self.__cookie_secure = "=".join([get_key_head_cookie, "'" + self.cookie.enc(self.path) + "'"])

    def __dec(self, path):
        get_dir = dir(self)
        if 'aes' in get_dir:
            path = path.replace('\'', '')
            split_get_key = str(path).split('=')
            get_key_head_cookie = split_get_key[0]
            self.path = path.replace(get_key_head_cookie, '')
            return "=".join([get_key_head_cookie, self.cookie.decode(self.path)])
        return path

    def crt(self, domain=None, h=None, m=None, **kwargs):
        utc = ''
        max_age, expires = [False, False]
        for x in kwargs:
            if 'max_age' in x.lower() and kwargs.get(x):
                max_age = True
            if 'expires' in x.lower() and kwargs.get(x):
                expires = True
        if expires and max_age:
            if h == None or h == False:
                h = 0
            if m == None or m == False:
                m = 0
            max_ages = self.exp * 86400
            max_ages = int(max_ages)
            utc = "Expires=" + UTC_DATE_TIME(d=self.exp, h=h, m=m).toUTC + " GMT; Max-Age=" + str(max_ages) + ";"
            utc = str(utc)
        elif expires and max_age == False:
            if h == None or h == False:
                h = 0
            if m == None or m == False:
                m = 0
            utc = "Expires=" + UTC_DATE_TIME(d=self.exp, h=h, m=m).toUTC + " GMT;"
        else:
            pass

        if domain:
            self.__cookie_secure = self.__cookie_secure + "; Domain=" + domain + "; " + utc
        else:
            self.__cookie_secure = self.__cookie_secure + "; " + utc
        return self.__cookie_secure