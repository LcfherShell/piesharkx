from datetime import timedelta, date, datetime, timezone
import calendar, time

__all__ = ["utc_mktime", "date_str", "datetime_next", "datetime_now", "datetime_UTF", "UTC_DATE_TIME", "TimeStamp"]

def utc_mktime(utc_tuple):
	if len(utc_tuple) == 6:
		utc_tuple += (0, 0, 0)
		return time.mktime(utc_tuple) - time.mktime((1970, 1, 1, 0, 0, 0, 0, 0, 0))
	return 0

class date_str:
	"""docstring for date_str"""
	def __init__(self, timed):
		super(date_str, self).__init__()
		self.toUTC:str = timed.strftime("%a, %d %b %Y %H:%M:%S")
		self.DateInt:int = timed.strftime('%Y%m%d')
		self.__call__(timed)
	def __call__(self, timed):
		self.datetime = str(timed)
	def __repr__ (self):
		return self.datetime
		
def datetime_next(datex_s:int):
	EndDate = date.today() + timedelta(days=datex_s)
	return int(EndDate.strftime('%Y%m%d'))

def datetime_now():
	EndDate = date.today()
	return int(EndDate.strftime('%Y%m%d'))

def datetime_UTF(datex_s):
	return str(datetime.now()+timedelta(days=datex_s))

def UTC_DATE_TIME(d:int=0, h:int=0, m:int=0):
	utc_dt = datetime.now(timezone.utc)+timedelta(days=d, hours=h, minutes=m)
	return date_str(utc_dt.astimezone())

def TimeStamp(date_time):
	if isinstance(date_time, tuple):
		try:
			data = calendar.timegm(date_time)
		except:
			
			data = int(utc_mktime(date_time.timetuple()))
	elif isinstance(date_time, dict):
		date_time = tuple(date_time)
		try:
			data = calendar.timegm(date_time)
		except:
			data = int(utc_mktime(date_time.timetuple()))
		
	else:
		if isinstance(date_time, int) or isinstance(date_time, str):
			data = date_time
		else:
			return
	return data
		#d = datetime.now(timezone.utc)
		#excute = datetime(datetime)