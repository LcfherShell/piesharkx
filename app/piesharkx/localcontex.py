import threading
from functools import partial
from collections import OrderedDict
import os
import time
import json
import hashlib
import sys
import signal
import logging
import inspect
import concurrent.futures
from datetime import datetime
import re
from werkzeug.wrappers import Request, Response

__all__ = [ "LocalProxy", "Local", "RequestContext", "_lookup_req_object", "_lookup_app_object"]

# Implementasi LocalProxy untuk piesharkX
class LocalProxy:
    """A proxy to the object bound to a local context."""
    
    def __init__(self, local, name=None):
        object.__setattr__(self, '_LocalProxy__local', local)
        object.__setattr__(self, '_LocalProxy__name', name)
    
    def _get_current_object(self):
        """Return the current object this proxy points to."""
        try:
            return self.__local()
        except RuntimeError:
            if self.__name is None:
                raise RuntimeError('object unbound')
            raise RuntimeError(f'object unbound: {self.__name}')
    
    @property
    def __dict__(self):
        try:
            return self._get_current_object().__dict__
        except RuntimeError:
            raise AttributeError('__dict__')
    
    def __repr__(self):
        try:
            obj = self._get_current_object()
        except RuntimeError:
            return f'<{self.__class__.__name__} unbound>'
        return repr(obj)
    
    def __bool__(self):
        try:
            return bool(self._get_current_object())
        except RuntimeError:
            return False
    
    def __getattr__(self, name):
        if name == '_LocalProxy__local':
            return object.__getattribute__(self, '_LocalProxy__local')
        elif name == '_LocalProxy__name':
            return object.__getattribute__(self, '_LocalProxy__name')
        else:
            return getattr(self._get_current_object(), name)
    
    def __setattr__(self, name, value):
        setattr(self._get_current_object(), name, value)
    
    def __delattr__(self, name):
        delattr(self._get_current_object(), name)
    
    def __getitem__(self, key):
        return self._get_current_object()[key]
    
    def __setitem__(self, key, value):
        self._get_current_object()[key] = value
    
    def __delitem__(self, key):
        del self._get_current_object()[key]
    
    def __call__(self, *args, **kwargs):
        return self._get_current_object()(*args, **kwargs)


class Local:
    """Local storage for request context."""
    
    def __init__(self):
        object.__setattr__(self, '__storage__', {})
        object.__setattr__(self, '__ident_func__', self._get_ident)
    
    def _get_ident(self):
        return threading.current_thread().ident
    
    def __getattr__(self, name):
        try:
            return self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)
    
    def __setattr__(self, name, value):
        ident = self.__ident_func__()
        storage = self.__storage__
        try:
            storage[ident][name] = value
        except KeyError:
            storage[ident] = {name: value}
    
    def __delattr__(self, name):
        try:
            del self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)
    
    def __release_local__(self):
        """Release the local context."""
        self.__storage__.pop(self.__ident_func__(), None)


# Context locals
_request_ctx_stack = threading.local()

class RequestContext:
    """The request context contains all request relevant information."""
    
    def __init__(self, app, environ):
        self.app = app
        self.request = Request(environ)
        self.session = {}
        self.g = type('g', (), {})()

    def __enter__(self):
        _request_ctx_stack.current = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(_request_ctx_stack, 'current'):
            del _request_ctx_stack.current



def _lookup_req_object(name):
    if not hasattr(_request_ctx_stack, 'current'):
        raise RuntimeError('Working outside of request context.')
    return getattr(_request_ctx_stack.current, name)

def _lookup_app_object(name):
    """Lookup app object."""
    if not hasattr(_request_ctx_stack, 'current') or _request_ctx_stack.current is None:
        raise RuntimeError('Working outside of application context.')

    return getattr(_request_ctx_stack.current.app, name)
