from .handler import OrderedDict, SelectType, create_secure_memory as Struct
from .main import current_app, request, session
from .handler.endecryptions import Base64_Token_128
from .date_moduler import datetime, datetime_next, datetime_now, datetime_UTF
import os, sys, statistics, chardet, json, uuid
from requests import Session
import functools, gc, uuid
#from Crypto import Random
#from Crypto.Cipher import AES
#from bs4 import BeautifulSoup
#from chardet import detect
__all__ = ["SESSION"]

class OBT_SESSION(SelectType):
	"""docstring for OBT_SESSION"""
	def __init__(self):
		super(OBT_SESSION, self).__init__()
		self.datetime_nw = datetime_now
		self.datetime_nxt = datetime_next
		self.datetime_utf = datetime_UTF

Struct = Struct('pieshark_session')
class SESSION(OBT_SESSION):
	def __init__(self, session:OrderedDict={}, app:str=None, by=2)->dict:
		super(SESSION, self).__init__()
		self.nows:int = self.datetime_nw()
		if app:
			self.developper = True
			self.environs = app.environ or os.environ
		else:
			self.developper = False
			self.environs = {}
		self.sv_date = by
		self.base64_ = Base64_Token_128(app)
		self.base64_.remove_function = True
		def _makes(self):
			_loop_key = 0
			while True:
				if _loop_key == 1:
					break
				else:
					try:
						self.base64_.Make_Key
						_loop_key +=1
					except:
						pass
			return self.base64_.key_mapp__(self.base64_)
		self.salt_key = _makes(self)

	def __repr__ (self)->None:
		gc.collect()
		objects = [i for i in gc.get_objects() if isinstance(i, functools._lru_cache_wrapper)]
		for object in objects:
			object.cache_clear()

		return session

	@property
	@functools.lru_cache(maxsize = None)
	def base(self):
		if session:
			for k, v in session.items():
				print(v)
				try:
					v = self.base64_.decode_base64(key=self.salt_key, message=str(v))
				except:
					del self.base64_.remove
					v = self.base64_.decode_base64(key=self.salt_key, message=str(v))
				session.update({k : v})
			return session
		return session

	@property
	@functools.lru_cache(maxsize = None)
	def insert(self):
		if id(self.developper) != 12:
			return session

	@insert.setter
	def insert(self, params:SelectType.Union_):
		if isinstance(params, SelectType.Dict_):
			try:
				for k, v in params.items():
					if isinstance(v, str):
						encypt = self.base64_.encode_base64(key=self.salt_key, message=str(v))
						session[str(k)] = encypt.encode()
					else:
						assert 1 != None
			except:
				del self.base64_.remove
		print("params:", params)
	@functools.lru_cache(maxsize = None)
	def get(self, params:str)->str:
		self.json = self.session
		if params in self.json:
			return self.json[params] or self.json.get(params)
		return

	@functools.lru_cache(maxsize = None)
	def update(self, params:str=None, new_value=None)->dict:
		if params and new_value:
			if isinstance(params, str):
				session[params] = new_value
		elif new_value:
			session[str(params)].update(new_value)

	@functools.lru_cache(maxsize = None)
	def pop(self, params:str=None)->None:
		if params:
			if isinstance(params, str):
				session.pop(params, None)