from piesharkx.main import pieshark, read_file, request, form, session
from piesharkx.blueprint import Blueprint
from piesharkx.sessions import SESSION
from piesharkx.cookies import Cookie
from piesharkx.templates import Templates
from piesharkx.pydejs import PY_deJS
import os,  json, time


pydejs = PY_deJS()

# Ambil library
pydejs.get(['jquery', 'bootstrap', 'lodash'], limit=5)

# Pilih dengan semua varian
pydejs.select_all(include_all_variants=True)

# Akses struktur bersarang
nested = pydejs.scripts_safe
jquery = nested.jquery
print("jquerymin" in jquery)
# auth_bp = Blueprint('auth', url_prefix='/auth')

# @auth_bp.route('/login', methods=['GET', 'POST'])
# async def login():
#     if session.get('user') == None:
#         return app.abort(404)
#     return "Login page"

# @auth_bp.route('/logout')
# async def logout():
#     print(2)
#     return "Logout"

# app = pieshark(True)
# app.config.update(dict(
#         secret_key = 'qxn203jsj02',
#         session_permanent=True,
#         url_dbase='base://sqlite3:static',
#         limit_size_upload=3089003
#     )
# )

# app.register_blueprint(auth_bp)

# cookie = Cookie(salt="tJHnN5b1i6wvXMwzYMRk128", app=app)

# deJS = PY_deJS()
# deJS.get(search=['jquery', 'bootstrap'], limit=5)
# deJS.select(['min', 'css'])
# print(deJS.scripts_safe.bootstrap)
# app.static('static/', '/static/')

# @app.route("/test-file/{filename}")
# def test_file_access(filename):
#     """Test file access functionality"""
#     static_folder = os.path.abspath("static")
#     file_path = os.path.join(static_folder, filename)
    
#     debug_info = {
#         "requested_file": filename,
#         "full_path": file_path,
#         "file_exists": os.path.exists(file_path),
#         "is_file": os.path.isfile(file_path),
#         "file_size": os.path.getsize(file_path) if os.path.exists(file_path) and os.path.isfile(file_path) else None,
#         "content_snippet": None
#     }
    
#     # Try to read a snippet of the file
#     if debug_info["file_exists"] and debug_info["is_file"]:
#         try:
#             with open(file_path, 'rb') as f:
#                 snippet = f.read(100)
#                 debug_info["content_snippet"] = str(snippet)
#                 debug_info["read_successful"] = True
#         except Exception as e:
#             debug_info["read_error"] = str(e)
#             debug_info["read_successful"] = False
#     return json.dumps(debug_info, indent=2)


# @app.route("/")
# async def home():
#     timestart = time.time()
#     session['user'] = f'Ramsyan{timestart}'
#     session['yudi'] = f'Ramsyan{timestart}'
#     session['user'] = f'Ramsyan{timestart}'
#     cookie.create(f"data=ssssssssssss{timestart}")
#     templates = """
#     <html>
#     <head>
#         <link rel="stylesheet" href="static/example.css">
#         <script>
#             alert('sss');
#         </script>
#     </head>
#     <body>
#         Hello from the HOME {{ hello }}
        
#         """
#     print(session['user'])
#     print(cookie.select.data) #mengambil data dari cookie default encrypt
#     print(cookie.select.data.decode()) #mengambil data dari cookie yang di decrypt
#     return Templates(templates, hello="mama")


# @app.route("/hello/{name}")
# async def greeting(name):
#     return f"Hello, {name}"
    
# @app.route("/about", methods=['POST', 'GET'])
# async def about():
#     method = request.method
#     if method in ["POST"]:
#         if form:
#             print(form.text) #mengambil data dari form default encrypt
#             print(form.text.decode()) #mengambil data dari form yang di decrypt
#     print(session.get('user'))
#     return Templates('example.shark')

# if __name__=='__main__':
#     app.run()