import os, sys, json
from io import BytesIO, StringIO, open as IOpen
from lxml.html import fromstring
from .handler import SelectType
from .handler.error_handler import ErrorHandler
from .handler.obfuscator import find_between, JS_Obfuscator
from jinja2 import Environment, FileSystemLoader, BaseLoader
from webob import Request, Response
import mimetypes
from json import JSONDecodeError
from typing import Any, Union
__all__ = ["Jinja2_Base_Templates", "allow_extent", "read_file", "Templates"]

def allow_extent(extend: SelectType.Union_) -> bool:
    """
    Check if file extension is supported by Jinja2 templating system.
    """
    return extend.lower() in ['html', 'html5', 'jinja2', 'jinja', 'shark']

class Jinja2_Base_Templates(SelectType):
    def __init__(self, base_html:SelectType.Union_) -> None:
        super(Jinja2_Base_Templates, self).__init__()
        if isinstance(base_html, bytes):
            self.decode_html_ = base_html.decode('utf-8')
        else:
            self.decode_html_ = str(base_html)

    def render(self, **kwargs) -> SelectType.Any_:
        """
        Render Jinja2 template with given kwargs.
        """
        if os.path.isfile(self.decode_html_):
            self.decode_html_ = read_file(self.decode_html_)
        try:
            template_dir = os.environ.get('templates', None)
            if template_dir and os.path.isdir(template_dir):
                    response_templates = Environment(loader=FileSystemLoader("templates/")).from_string(self.decode_html_)
            else:
                response_templates = Environment(loader=BaseLoader).from_string(self.decode_html_)
        except:
            response_templates = Environment(loader=BaseLoader).from_string(self.decode_html_)
        return response_templates.render(**kwargs)


_file_cache = {}
def read_file(file_name: str, cache: bool = True) -> str:
    """
    Read file content with optional per-file cache.

    Args:
        file_name (str): Path to file.
        cache (bool): Whether to cache the content.

    Returns:
        str: Content of the file.
    """
    global _file_cache

    if cache and file_name in _file_cache:
        return _file_cache[file_name]

    if not os.path.isfile(file_name):
        raise FileNotFoundError(f"File '{file_name}' not found")

    def try_utf8(data: bytes) -> str:
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data.decode('latin1')  # Fallback

    with IOpen(file_name, "rb", buffering=0) as f:
        raw = f.read()
        content = try_utf8(raw)

    if cache:
        _file_cache[file_name] = content

    return content

def jsonparsing(data: Union[str, dict, list]) -> Any:
    """
    Recursively parses a JSON string or structure into Python objects.
    If input is a string, it tries to parse it as JSON.
    If it's a dict or list, it recursively processes all elements.

    Args:
        data (Union[str, dict, list]): The input data to parse.

    Returns:
        Any: Parsed data, or None if parsing fails.
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)

        if isinstance(data, dict):
            return {k: jsonparsing(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [jsonparsing(item) for item in data]

        else:
            return data  # base case for primitives: int, float, bool, etc.

    except (JSONDecodeError, TypeError):
        return None

#####TEMPLATES
session_bytes = bytes(''.encode('utf-8'))
def Templates(filename: str, **kwargs):
    try:
        # Buka file dalam mode biner
        with IOpen(filename, "rb") as file:
            content = file.read()

        ext = os.path.splitext(filename)[1][1:].strip().lower()

        if ext in ['shark', 'jshark', 'json'] or allow_extent(ext):
            try:
                content_decoded = content.decode()
            except UnicodeDecodeError as e:
                raise UnicodeDecodeError(e)
        else:
            # File tidak dikenali, langsung return raw content
            return content

    except Exception:
        # Jika gagal membaca file, asumsi input adalah string literal
        content_decoded = filename
        ext = os.path.splitext(filename)[1][1:].strip().lower()

    # Jika file JSON atau mirip, parse sebagai JSON
    if ext in ["json", "jshark"]:
        parsed = jsonparsing(content_decoded)
        if parsed is not None:
            return parsed
        else:
            return None

    # Jika ada blok obfuscated JS, deobfuscate
    if '{ obfusc_js }' in content_decoded:
        try:
            content_decoded = content_decoded.encode('utf-8').decode('utf-8')  # Ensures UTF-8 string
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(e)
        
        js_code = find_between(content_decoded, first='{ obfusc_js }', last='{ endobfusc_js }')
        content_decoded = content_decoded.replace('{ obfusc_js }', '')
        content_decoded = content_decoded.replace('{ endobfusc_js }', '')

        obfuscator = JS_Obfuscator()
        deobfuscated = obfuscator.javascript_start(str(js_code))

        content_decoded = content_decoded.replace(js_code, deobfuscated)

    # Render Jinja2 template
    rendered = Jinja2_Base_Templates(content_decoded).render(**kwargs)
    return bytes(rendered.encode('utf-8'))

def html_parser(data, select):
    doc = fromstring(data)
    return "".join(filter(None, (e.text for e in doc.cssselect(select)[0])))

def ge_typ(filename):
    type, encoding = mimetypes.guess_type(filename)
    return type or 'application/octet-stream'

def read_file_byets(data, **kwargs):
    if os.path.isfile(data) == True:
        try:
            _read_file_ = read_file(data)
            for key in kwargs.keys():
                if f'{{ key }}' in _read_file_:
                    _read_file_ = _read_file_.replace(f'{{ key }}', kwargs[key])
        except:
            pass
    else:
        _read_file_ = data

    session_bytes = bytes(_read_file_.encode('utf-8'))
    return session_bytes