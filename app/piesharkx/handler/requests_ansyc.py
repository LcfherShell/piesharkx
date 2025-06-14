import asyncio, time, timeit
from requests import Session
from typing import Callable, List, Optional, Any, Coroutine
from requests import Session
from concurrent.futures import ThreadPoolExecutor
try:
    from ..handler import OrderedDict, SelectType, create_secure_memory as Struct
except:
    from . import OrderedDict, SelectType, create_secure_memory as Struct

__all__ = ["REQUESTS"]

#from .handler import OrderedDict, SelectType, Struct
def timer(number=1, repeat=1):
    """Timer decorator to measure average execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            def _run():
                return func(*args, **kwargs)

            duration = timeit.repeat(_run, number=number, repeat=repeat)
            avg = sum(duration) / len(duration)
            print(f"[TIMER] Avg: {avg:.4f} seconds over {repeat} run(s)")
            return func(*args, **kwargs)
        return wrapper
    return decorator

output = []
Struct = Struct('requests')
class REQUESTS(Session, SelectType):
    """
    Enhanced requests session with async and callback-based control,
    integrated with secure struct storage.
    """

    def __init__(self):
        super().__init__()
        self.params: dict = OrderedDict()
        self.stream: bool = False
        self.verify: bool = True
        self.value = Struct()

    @classmethod
    def __subclasscheck__(cls, sub):
        return hasattr(sub, 'request') and callable(sub.request)

    # === LOW LEVEL ASYNC ===
    async def async_requests(self, sites_list: List[str], min_loop: int = 1, max_loop: int = 2) -> tuple:
        """
        Execute multiple async GET requests using threads.
        """
        if not sites_list:
            raise ValueError("sites_list cannot be empty.")

        max_loop = min(max_loop, len(sites_list))  # Avoid overflow
        response_html = ()

        with ThreadPoolExecutor(max_workers=max_loop) as executor:
            loop = asyncio.get_running_loop()
            futures = [
                loop.run_in_executor(
                    executor, 
                    self._safe_request, 
                    sites_list[i]
                )
                for i in range(min(min_loop, len(sites_list)))
            ]

            responses = await asyncio.gather(*futures, return_exceptions=True)
            response_html += tuple(responses)
        try:
            self.value.insert_dict = {'response': response_html}
        except:
            self.value.update_dict = {'response': response_html}
        return response_html

    def _safe_request(self, url: str):
        """
        Safely perform GET request, with basic error handling.
        """
        try:
            return self.get(url, params=self.params, stream=self.stream, verify=self.verify)
        except Exception as e:
            return f"[ERROR] Failed to fetch {url}: {str(e)}"

    # === HIGH LEVEL CALLBACK ===
    def requests_ncache(self, callback: Optional[Callable[[Any], Any]] = None):
        """
        Decorator for request-based function with optional result callback.
        Automatically updates self.value.
        """
        def inner(func: Callable[..., Any]):
            def wrapper(*args, **kwargs) -> Coroutine:
                async def _execute():
                    result = await asyncio.to_thread(func, *args, **kwargs)

                    if callable(callback):
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(result)
                            else:
                                callback(result)
                        except Exception as cb_err:
                            print(f"[Callback Error] {cb_err}")

                    self.value.update_dict = {'response': result}
                    return result

                return asyncio.ensure_future(_execute())

            return wrapper

        return inner

app = REQUESTS()



#import requests

# Must provide a callback function, callback func will be executed after the func completes execution !!

#app = REQUESTS()
#@req.requests_ncache(callback=lambda res: print("[Callback Output]", res))
#def get(url):
#    return requests.get(url, stream=True)



#print('Low:')
#loop = asyncio.get_event_loop()
#response=loop.run_until_complete(app.async_requests(['http://www.google.com', 'http://www.github.com'], min_loop=2, max_loop=3))
#for pages in response:
#    print(pages.content)

#print('\n\nHight:')
#asyncio.run(get_example())



"""async def main():
    loop = asyncio.get_event_loop()
    future1 = loop.run_in_executor(None, requests.get, 'http://www.google.com')
    future2 = loop.run_in_executor(None, requests.get, 'http://www.google.co.uk')
    response1 = await future1
    response2 = await future2
    print(response1.text)
    print(response2.text)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())"""