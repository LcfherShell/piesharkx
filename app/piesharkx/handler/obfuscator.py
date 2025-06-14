import os, requests
import random
import re
import string
import sys
import uuid
import asyncio
from typing import Callable, Dict, Tuple
from requests_html import HTML

__all__ = ["map_script", "JS_Obfuscator"]

dir_path = os.path.dirname(os.path.realpath(__file__))
path = os.path.normpath(dir_path)
path_split = path.split(os.sep)
dir_path = dir_path.replace(path_split[len(path_split)-1], 'js/JSObus.js')
if os.path.isfile(dir_path):
    pass
else:
    assert 2==2

def find_between( s:str, first:str, last:str):
    def class_find():
        try:
            start = s.index( first ) + len( first )
            end = s.index( last, start )
            return s[start:end]
        except ValueError:
            result = re.search('%s(.*)%s' % (first, last), s).group(1)
            return result
    if first in s and last in s: return class_find()
    return ''
    
def find_between_r( s:str, first:str, last:str):
    def class_find():
        try:
            start = s.rindex( first ) + len( first )
            end = s.rindex( last, start )
            return s[start:end]
        except ValueError:
            pass
        return ""
    if first in s and last in s: return class_find()
    return ''


def reads():
    with open(dir_path.replace('\\', '/'), 'rb') as f:
        return f.read()

class map_script:
    data_js =  """<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/javascript-obfuscator/dist/index.browser.js"></script>"""
    string_js = """<script type="text/javascript">{path_js}</script>""".format(path_js=reads())


class JS_Obfuscator(map_script):
    """docstring for Obuscator"""
    def __init__(self, files=''):
        super(JS_Obfuscator, self).__init__()
        self.files = files
    
    @property
    def unic_html5(self):
        try:
            with requests.get('https://www.google.com', timeout=2) as resu:
                javascript_obfuscator= self.data_js
        except:
            javascript_obfuscator = self.string_js
        return javascript_obfuscator

    def javascript_start(self, payload:str):
        script = """
        function escramble_758(){
                var obfuscationResult = JavaScriptObfuscator.obfuscate(
                `
                 """
        payload = str(payload)
        end_script = """
                `,
                {
                    compact: false,
                    controlFlowFlattening: true,
                    controlFlowFlatteningThreshold: 1,
                    numbersToExpressions: true,
                    simplify: true,
                    stringArrayShuffle: true,
                    splitStrings: true,
                    stringArrayThreshold: 1
                }
                );
                var response = obfuscationResult.getObfuscatedCode()
                return response.toString();
        }"""
        if os.path.isfile(self.files):
            with open(self.files, 'rb') as f:
                html5_response = f.read()
        else:
            html5_response = '<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/javascript-obfuscator/dist/index.browser.js"></script>'

        jscript = "".join([str(script), payload, str(end_script)])
        html = HTML(html=html5_response)

        # 👇 Cek dan buat event loop secara manual jika perlu
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return html.render(script=jscript, reload=False)
        
