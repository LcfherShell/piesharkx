from typing import TypeVar, Generic, Any, Union, Optional, Set
from logging import Logger
from collections.abc import Iterable
from collections import OrderedDict
import os, re, abc, copy
from threading import Lock
import weakref
from functools import wraps
import inspect
import sys, json

__all__ = ["create_secure_memory", "Socket_Error", "Do_Under", "Typping", "AbstractClass",
    "Handlerr", "ErrorHandler", "HTTPException", "BadRequest", 
    "Unauthorized", "Forbidden", "NotFound", "MethodNotAllowed", 
    "InternalServerError", "HTTPExceptions", "PieSharkErrorMixin",
    "error_handler_decorator", "ErrorContext", "ErrorLogger", "NetworkScanner", "NetworkServer",
    "REQUESTS", "JS_Obfuscator", "SelectType", "replace_special_chars", "clean_json",
    "AdvancedCryptoSystem", "Base64_Token_128", "Ciphertext_128", "Magic_Data", 
    "AESCipher", "AUTH_TOKEN", "AESCipher_2", "AES", "base64", "hashlib"
    ]

class SelectType:
    Union_ = Union[int, str, float, list, tuple, dict, bool, bytes]
    Any_ = Any
    Dict_ = dict
    List_ = Union[list, tuple]
    Ordered_ = OrderedDict()


def replace_special_chars(input_string):
    if not isinstance(input_string, str):
        raise TypeError("Input must be a string.")

    # Remove extra spaces and replace with underscore
    input_string = "_".join(input_string.strip().split())

    if not input_string:
        raise ValueError("Input string is empty after trimming and space replacement.")

    # Separate digits at the beginning
    match = re.match(r"^(\d+)([a-zA-Z_].*)?", input_string)
    if match:
        digits = match.group(1)
        rest = match.group(2) or ""
        input_string = rest + "_" + digits

    # If result is only digits, it's invalid
    if input_string.isdigit():
        raise ValueError(
            "Resulting string contains only digits, which is not a valid name."
        )

    # Replace all non-alphanumeric and non-underscore characters with "_"
    output_string = re.sub(r"[^a-zA-Z0-9_]", "_", input_string)

    if output_string.replace("_", "").__len__() <= 0:
        raise ValueError("Input string is empty after trimming and space replacement.")

    # Strip leading/trailing underscores
    return output_string.strip("_")


def is_all_list(data):
    return all(isinstance(i, list) for i in data)


def clean_json(raw_data: dict):
    # Bersihkan key-key menggunakan fungsi
    cleaned_data = {}
    for key, value in raw_data.items():
        try:
            cleaned_key = replace_special_chars(key)
            cleaned_data[cleaned_key] = value
        except ValueError as e:
            pass
        except TypeError as e:
            pass
    return cleaned_data

from memoryawarestruct import create_secure_memory
from .endecryptions import (AdvancedCryptoSystem, 
    Base64_Token_128, Ciphertext_128, Magic_Data, 
    AESCipher, AUTH_TOKEN, AESCipher_2, AES, 
    base64, hashlib)
from .error_handler import (
    Socket_Error, Do_Under, Typping, AbstractClass,
    Handlerr, ErrorHandler, HTTPException, BadRequest, 
    Unauthorized, Forbidden, NotFound, MethodNotAllowed, 
    InternalServerError, HTTPExceptions, PieSharkErrorMixin,
    error_handler_decorator, ErrorContext, ErrorLogger)
from .handshake import NetworkScanner, NetworkServer
from .requests_ansyc import REQUESTS
from .obfuscator import JS_Obfuscator

