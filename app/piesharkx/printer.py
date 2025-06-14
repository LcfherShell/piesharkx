import json, re
import time
import logging
import builtins
import types
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    print("Warning: colorama not installed. Install with: pip install colorama")
    COLORAMA_AVAILABLE = False
    # Fallback color constants
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ""

__all__ = ["mainPrinter"]

def remove_multispace(text: str) -> str:
    return text
# Enhanced Console Output System (Node.js style)
class ConsoleFormatter:
    """Advanced console formatter with type-aware coloring"""
    
    @staticmethod
    def format_value(value: Any, indent: int = 0) -> str:
        """Format any value with appropriate colors based on type"""
        indent_str = "  " * indent
        next_indent = "  " * (indent + 1)

        if value is None:
            return f"{Fore.MAGENTA}null{Style.RESET_ALL}"
        elif isinstance(value, bool):
            return f"{Fore.YELLOW}{str(value).lower()}{Style.RESET_ALL}"
        elif isinstance(value, str):
            return f"{Fore.GREEN}'{value}'{Style.RESET_ALL}"
        elif isinstance(value, int):
            return f"{Fore.CYAN}{value}{Style.RESET_ALL}"
        elif isinstance(value, float):
            return f"{Fore.CYAN}{value:.3f}{Style.RESET_ALL}"
        elif isinstance(value, list):
            if not value:
                return f"{Fore.MAGENTA}[]{Style.RESET_ALL}"
            
            items = []
            for i, item in enumerate(value[:10]):
                formatted_item = ConsoleFormatter.format_value(item, indent + 1)
                items.append(f"{next_indent}{formatted_item}")
            
            if len(value) > 10:
                items.append(f"{next_indent}{Fore.WHITE}... +{len(value) - 10} more{Style.RESET_ALL}")

            return (
                f"{Fore.MAGENTA}[{Style.RESET_ALL}"
                + ", ".join(items).strip()
                + f"{indent_str}{Fore.MAGENTA}]{Style.RESET_ALL}"
            )
        elif isinstance(value, dict):
            return ConsoleFormatter.format_dict(value, indent)
        elif isinstance(value, types.FunctionType):
            return f"{Fore.BLUE}Function{Style.RESET_ALL}: {Fore.WHITE}{value.__name__}(){Style.RESET_ALL}"
        elif isinstance(value, type):
            return f"{Fore.MAGENTA}Class{Style.RESET_ALL}: {Fore.WHITE}{value.__name__}{Style.RESET_ALL}"
        elif hasattr(value, '__class__'):
            return f"{Fore.MAGENTA}{value.__class__.__name__}{Style.RESET_ALL}: {Fore.WHITE}{str(value).strip()}{Style.RESET_ALL}"
        else:
            return f"{Fore.WHITE}{str(value).strip()}{Style.RESET_ALL}"
    
    @staticmethod
    def format_dict(data: dict, indent: int = 0) -> str:
        """Format dictionary with proper JSON-like structure"""
        if not data:
            return f"{Fore.YELLOW}{{}}{Style.RESET_ALL}"
            
        indent_str = "  " * indent
        next_indent = "  " * (indent + 1)
        
        items = []
        for key, value in data.items():
            formatted_key = f"{Fore.BLUE}'{key.strip()}'{Style.RESET_ALL}" if isinstance(key, str) else ConsoleFormatter.format_value(key)
            formatted_value = ConsoleFormatter.format_value(value, indent + 1)
            items.append(f"{next_indent}{formatted_key}: {formatted_value.strip()}")
        
        return f"{Fore.YELLOW}{{{Style.RESET_ALL}\n" + ",\n".join(items) + f"\n{indent_str}{Fore.YELLOW}}}{Style.RESET_ALL}"

# Store original print function
def mainPrinter():
    original_print = builtins.print

    def console_log(*args, **kwargs) -> None:
        """Enhanced print function with Node.js style formatting"""
        if not args:
            original_print()
            return
        
        # Format each argument
        formatted_args = []
        for arg in args:
            formatted_args.append(ConsoleFormatter.format_value(arg))
        
        # Create log prefix
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_prefix = f"{Fore.CYAN}{Style.BRIGHT}[{timestamp}]{Style.RESET_ALL}"
        
        # Join formatted arguments
        output = remove_multispace(" ".join(formatted_args).strip())
        
        # Print with prefix
        original_print(f"{log_prefix} {output}", **kwargs)

    builtins.print = console_log