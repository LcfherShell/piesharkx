import os, json, time
from .handler import OrderedDict, SelectType, create_secure_memory
from .handler.error_handler import PieSharkErrorMixin

__all__ = ["config", "config_pieshark"]

class config:
    def __init__(self, config:SelectType.Dict_):
        self.config = config
    
    def insert(self, *args,  **kwargs):
        if args:
            if isinstance(args[0], dict):
                kwargs =  args[0]
        self.config.insert_dict = kwargs
        
    def update(self, *args, **kwargs):
        if args:
            if isinstance(args[0], dict):
                kwargs =  args[0]
        try:
            self.config.update_dict = kwargs
        except:
            self.config.insert_dict = kwargs
    
    def delete(self, keys:str):
        self.config.dell_dict(keys)

    def pop(self, keys:str):
        time.sleep(0.12)
        self.config.dell_dict(keys)


class config_pieshark(PieSharkErrorMixin):
    def __init__(self, debug=True, **kwargs):
        self.configt:SelectType.Dict_ = None
        super().__init__(debug=debug, **kwargs)
    @property
    def config(self):
        return config(self.configt)