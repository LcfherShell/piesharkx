# 🦈 PieSharkX Framework - Dokumentasi Lengkap
*Framework Web Python yang Ringan, Powerful, dan Modern*

---

## 📖 Daftar Isi

1. [Pengenalan](#pengenalan)
2. [Instalasi & Setup](#instalasi--setup)
3. [Quick Start](#quick-start)
4. [Routing System](#routing-system)
5. [Request & Response](#request--response)
6. [Template System](#template-system)
7. [Session & Cookie Management](#session--cookie-management)
8. [Blueprint System](#blueprint-system)
9. [Security Features](#security-features)
10. [Static Files](#static-files)
11. [Form Processing & File Upload](#form-processing--file-upload)
12. [Middleware & Hooks](#middleware--hooks)
13. [API Development](#api-development)
14. [CLI Tools](#cli-tools)
15. [Database Integration](#database-integration)
16. [Utilities](#utilities)
17. [Testing](#testing)
18. [Deployment](#deployment)
19. [Best Practices](#best-practices)
20. [Troubleshooting](#troubleshooting)

---

## 🚀 Pengenalan

**PieSharkX** adalah framework web Python modern yang dibangun dengan prinsip kesederhanaan tanpa mengorbankan kekuatan. Framework ini menyediakan semua tools yang dibutuhkan untuk membangun aplikasi web dan API yang robust dengan sintaks yang clean dan mudah dipahami.

### ✨ Fitur Utama

- 🛣️ **Routing Fleksibel** - Mendukung path parameters, regex patterns, dan RESTful endpoints
- 🔐 **Keamanan Built-in** - Enkripsi otomatis untuk session dan cookie
- 🧩 **Arsitektur Modular** - System Blueprint untuk organisasi kode yang baik
- ⚡ **Dukungan Async/Sync** - Native support untuk handler synchronous dan asynchronous
- 🎨 **Template Engine** - Template engine ringan dengan Python variable injection
- 🔧 **Middleware Ready** - Dukungan custom middleware untuk request/response processing
- 📦 **Static File Serving** - Built-in static file handling
- 🛠️ **CLI Tools** - Command line interface lengkap untuk development
- 🌐 **WSGI Compatible** - Kompatibel dengan server WSGI standar

### 🏆 Keunggulan PieSharkX

| Fitur | PieSharkX | Framework Lain |
|-------|-----------|----------------|
| **Learning Curve** | Minimal | Steep |
| **Built-in Security** | ✅ Enkripsi otomatis | ❌ Setup manual |
| **Async Support** | ✅ Native | ⚠️ Butuh plugin |
| **File Size** | Ringan | Berat |
| **Flexibility** | Tinggi | Sedang |
| **CLI Tools** | ✅ Lengkap | ⚠️ Terbatas |

---

## 🔧 Instalasi & Setup

### Persyaratan Sistem

- Python 3.7+
- pip (Python package manager)

### Instalasi Framework

```bash
# Instalasi dari PyPI (jika tersedia)
pip install piesharkx

# Atau instalasi dari source
git clone https://github.com/username/piesharkx.git
cd piesharkx
pip install -e .

# Instalasi dependencies tambahan untuk CLI
pip install click watchdog
```

### Struktur Project Dasar

```
myproject/
├── app.py                 # File aplikasi utama
├── config.py              # Konfigurasi aplikasi
├── requirements.txt       # Dependencies
├── static/                # File statis
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # Template files
└── blueprints/            # Module aplikasi
    ├── __init__.py
    ├── auth.py
    └── api.py
```

---

## 🚀 Quick Start

### Aplikasi Sederhana

```python
# app.py
from piesharkx.main import pieshark, request, form, session
from piesharkx.templates import Templates

# Inisialisasi aplikasi
app = pieshark(debug=True)

# Konfigurasi aplikasi
app.config.update({
    'secret_key': 'your-super-secret-key-here',
    'session_permanent': True,
    'url_dbase': 'base://sqlite3:static',
    'limit_size_upload': 3089003  # ~3MB upload limit
})

# Route pertama
@app.route("/")
async def home():
    return "Hello, PieSharkX!"

# Route dengan template
@app.route("/welcome/{name}")
async def welcome(name):
    return Templates(
        "<h1>Selamat datang, {{ name }}!</h1>", 
        name=name
    )

# Jalankan aplikasi
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```

### Menjalankan Aplikasi

```bash
# Menjalankan langsung
python app.py

# Atau menggunakan CLI
pieshark run

# Dengan opsi development
pieshark run --debug --reload --host 0.0.0.0 --port 8000
```

---

## 🛣️ Routing System

PieSharkX menyediakan sistem routing yang fleksibel untuk berbagai kebutuhan aplikasi.

### Basic Routing

```python
@app.route("/")
async def index():
    return "Homepage"

@app.route("/about")
def about():
    return "About Page"

# Route dengan parameter
@app.route("/user/{user_id}")
async def get_user(user_id):
    return f"User ID: {user_id}"

# Multiple parameters
@app.route("/user/{user_id}/post/{post_id}")
async def get_user_post(user_id, post_id):
    return f"User {user_id}, Post {post_id}"
```

### HTTP Methods

```python
@app.route("/api/data", methods=["GET", "POST", "PUT", "DELETE"])
async def handle_data():
    if request.method == "GET":
        return app.json_response({"data": "sample"})
    
    elif request.method == "POST":
        # Handle POST data
        return app.json_response({"created": True}, status=201)
    
    elif request.method == "PUT":
        # Handle PUT data
        return app.json_response({"updated": True})
    
    elif request.method == "DELETE":
        # Handle DELETE
        return app.json_response({"deleted": True})
```

### Regex Routing

```python
# Pattern regex untuk routing advanced
@app.route("^/api/user/(\d+)$", methods=["GET"])
async def get_user_regex(user_id):
    return app.json_response({
        "user_id": int(user_id),
        "type": "regex_route"
    })

# Pattern untuk email
@app.route("^/profile/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$")
async def profile_by_email(email):
    return f"Profile for: {email}"
```

### Route Decorators & Helpers

```python
# Route dengan kondisi
@app.route("/admin/dashboard")
async def admin_dashboard():
    if not session.get('is_admin'):
        return app.abort(403)
    return "Admin Dashboard"

# Redirect
@app.route("/old-page")
async def old_page():
    return app.redirect("/new-page", code=301)

# Error handling
@app.route("/error-demo")
async def error_demo():
    return app.abort(404, "Page not found")
```

---

## 📡 Request & Response

### Request Object

```python
from piesharkx.main import request

@app.route("/request-info", methods=["GET", "POST"])
async def request_info():
    info = {
        "method": request.method,
        "path": request.path,
        "query_string": request.query_string,
        "headers": dict(request.headers),
        "user_agent": request.headers.get('User-Agent'),
        "remote_addr": request.environ.get('REMOTE_ADDR'),
        "content_length": request.content_length
    }
    
    return app.json_response(info)
```

### Query Parameters

```python
@app.route("/search")
async def search():
    # Mengakses query parameters
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    return app.json_response({
        "query": query,
        "page": page,
        "per_page": per_page,
        "all_args": dict(request.args)
    })
```

### JSON Data

```python
@app.route("/api/data", methods=["POST"])
async def handle_json():
    try:
        data = request.get_json()
        if not data:
            return app.json_response({"error": "No JSON data"}, status=400)
        
        # Process data
        return app.json_response({
            "received": data,
            "status": "success"
        })
    except Exception as e:
        return app.json_response({"error": str(e)}, status=400)
```

### Response Types

```python
# JSON Response
@app.route("/api/users")
async def get_users():
    users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
    return app.json_response(users)

# Custom headers
@app.route("/api/custom")
async def custom_response():
    response = app.json_response({"data": "custom"})
    response.headers['X-Custom-Header'] = 'MyValue'
    response.headers['Cache-Control'] = 'no-cache'
    return response

# File download
@app.route("/download/{filename}")
async def download_file(filename):
    return app.send_file(f"uploads/{filename}", as_attachment=True)
```

---

## 🎨 Template System

PieSharkX menyediakan template engine yang sederhana namun powerful.

### Basic Templating

```python
from piesharkx.templates import Templates

@app.route("/template-demo")
async def template_demo():
    return Templates("""
        <html>
        <head><title>{{ title }}</title></head>
        <body>
            <h1>{{ heading }}</h1>
            <p>User: {{ user.name }}</p>
            <p>Email: {{ user.email }}</p>
        </body>
        </html>
    """, 
    title="Demo Page",
    heading="Welcome to PieSharkX",
    user={"name": "John Doe", "email": "john@example.com"}
    )
```

### File-based Templates

```python
# templates/base.shark
"""
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
    </nav>
    <main>
        {{ content }}
    </main>
</body>
</html>
"""

@app.route("/page")
async def page():
    return Templates("base.shark", 
                    title="My Page",
                    content="<h1>Page Content</h1>")
```

### Template dengan Loop & Kondisi

```python
@app.route("/products")
async def products():
    products = [
        {"name": "Laptop", "price": 1000, "in_stock": True},
        {"name": "Mouse", "price": 25, "in_stock": True},
        {"name": "Monitor", "price": 300, "in_stock": False}
    ]
    
    template = """
    <div class="products">
        {% for product in products %}
            <div class="product {{ 'in-stock' if product.in_stock else 'out-of-stock' }}">
                <h3>{{ product.name }}</h3>
                <p>Price: ${{ product.price }}</p>
                {% if product.in_stock %}
                    <button>Add to Cart</button>
                {% else %}
                    <span>Out of Stock</span>
                {% endif %}
            </div>
        {% endfor %}
    </div>
    """
    
    return Templates(template, products=products)
```

### Template Helpers

```python
# Custom template functions
def format_currency(amount):
    return f"${amount:,.2f}"

def format_date(date):
    return date.strftime("%B %d, %Y")

# Gunakan dalam template
@app.route("/invoice/{invoice_id}")
async def invoice(invoice_id):
    invoice_data = get_invoice(invoice_id)  # Your data logic
    
    return Templates("invoice.shark",
                    invoice=invoice_data,
                    format_currency=format_currency,
                    format_date=format_date)
```

---

## 🔐 Session & Cookie Management

PieSharkX menyediakan sistem session dan cookie yang aman dengan enkripsi otomatis.

### Session Management

```python
from piesharkx.main import session

@app.route("/login", methods=["GET", "POST"])
async def login():
    if request.method == "POST":
        username = form.username.decode()
        password = form.password.decode()
        
        # Authenticate user (your logic)
        if authenticate_user(username, password):
            # Session otomatis terenkripsi
            session['user_id'] = 12345
            session['username'] = username
            session['roles'] = ['user', 'admin']
            session['login_time'] = datetime.now().isoformat()
            
            return app.redirect("/dashboard")
        else:
            return Templates("login.shark", error="Invalid credentials")
    
    return Templates("login.shark")

@app.route("/dashboard")
async def dashboard():
    if not session.get('user_id'):
        return app.redirect("/login")
    
    return Templates("""
        <h1>Welcome, {{ username }}!</h1>
        <p>User ID: {{ user_id }}</p>
        <p>Roles: {{ roles }}</p>
        <a href="/logout">Logout</a>
    """, 
    username=session['username'],
    user_id=session['user_id'],
    roles=', '.join(session['roles'])
    )

@app.route("/logout")
async def logout():
    session.clear()
    return app.redirect("/")
```

### Cookie Management

```python
from piesharkx.cookie import Cookie

# Inisialisasi cookie handler
cookie = Cookie(salt="your_custom_salt", app=app)

@app.route("/set-preferences", methods=["POST"])
async def set_preferences():
    theme = form.theme.decode()
    language = form.language.decode()
    
    # Cookie otomatis terenkripsi
    cookie.create(f"theme={theme}&language={language}&timezone=UTC")
    
    return app.json_response({"status": "preferences saved"})

@app.route("/get-preferences")
async def get_preferences():
    # Decrypt dan baca cookie data
    theme = cookie.select.theme.decode() or "light"
    language = cookie.select.language.decode() or "en"
    timezone = cookie.select.timezone.decode() or "UTC"
    
    return app.json_response({
        "theme": theme,
        "language": language,
        "timezone": timezone
    })

@app.route("/clear-preferences")
async def clear_preferences():
    cookie.delete()
    return app.json_response({"status": "preferences cleared"})
```

### Session Configuration

```python
app.config.update({
    'secret_key': 'your-super-secret-key-here',
    'session_permanent': True,
    'session_lifetime': 3600,  # 1 hour in seconds
    'session_cookie_name': 'piesharkx_session',
    'session_cookie_domain': None,
    'session_cookie_path': '/',
    'session_cookie_httponly': True,
    'session_cookie_secure': False,  # Set True for HTTPS
    'session_cookie_samesite': 'Lax'
})
```

---

## 🧩 Blueprint System

Blueprint memungkinkan Anda mengorganisir aplikasi menjadi modul-modul yang terpisah.

### Basic Blueprint

```python
# blueprints/auth.py
from piesharkx.blueprint import Blueprint
from piesharkx.main import request, form, session
from piesharkx.templates import Templates

auth_bp = Blueprint('auth', url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        username = form.username.decode()
        password = form.password.decode()
        
        if authenticate(username, password):
            session['user'] = username
            return app.redirect('/dashboard')
        else:
            return Templates("auth/login.shark", error="Invalid credentials")
    
    return Templates("auth/login.shark")

@auth_bp.route('/register', methods=['GET', 'POST'])
async def register():
    if request.method == 'POST':
        username = form.username.decode()
        email = form.email.decode()
        password = form.password.decode()
        
        # Registration logic
        if create_user(username, email, password):
            return app.redirect('/auth/login')
        else:
            return Templates("auth/register.shark", error="Registration failed")
    
    return Templates("auth/register.shark")

@auth_bp.route('/logout')
async def logout():
    session.clear()
    return app.redirect('/')

# Register blueprint di app utama
# app.py
from blueprints.auth import auth_bp
app.register_blueprint(auth_bp)
```

### API Blueprint

```python
# blueprints/api.py
from piesharkx.blueprint import Blueprint

api_bp = Blueprint('api', url_prefix='/api/v1')

@api_bp.route('/users', methods=['GET'])
async def list_users():
    users = get_all_users()  # Your data logic
    return app.json_response({
        "users": users,
        "count": len(users),
        "status": "success"
    })

@api_bp.route('/users/{user_id}', methods=['GET', 'PUT', 'DELETE'])
async def handle_user(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if not user:
            return app.json_response({"error": "User not found"}, status=404)
        return app.json_response(user)
    
    elif request.method == 'PUT':
        data = request.get_json()
        updated_user = update_user(user_id, data)
        return app.json_response(updated_user)
    
    elif request.method == 'DELETE':
        if delete_user(user_id):
            return app.json_response({"message": "User deleted"})
        return app.json_response({"error": "User not found"}, status=404)

@api_bp.route('/posts', methods=['GET', 'POST'])
async def handle_posts():
    if request.method == 'GET':
        posts = get_all_posts()
        return app.json_response(posts)
    
    elif request.method == 'POST':
        data = request.get_json()
        new_post = create_post(data)
        return app.json_response(new_post, status=201)

# Register di app utama
from blueprints.api import api_bp
app.register_blueprint(api_bp)
```

### Blueprint dengan Middleware

```python
# blueprints/admin.py
admin_bp = Blueprint('admin', url_prefix='/admin')

@admin_bp.before_request
def require_admin():
    """Middleware untuk semua route admin"""
    if not session.get('is_admin'):
        return app.abort(403, "Admin access required")

@admin_bp.route('/dashboard')
async def admin_dashboard():
    stats = get_admin_stats()
    return Templates("admin/dashboard.shark", stats=stats)

@admin_bp.route('/users')
async def manage_users():
    users = get_all_users_admin()
    return Templates("admin/users.shark", users=users)

@admin_bp.route('/settings', methods=['GET', 'POST'])
async def admin_settings():
    if request.method == 'POST':
        # Update settings logic
        update_settings(request.get_json())
        return app.json_response({"status": "updated"})
    
    settings = get_current_settings()
    return Templates("admin/settings.shark", settings=settings)
```

---

## 🔒 Security Features

PieSharkX memiliki berbagai fitur keamanan built-in.

### CSRF Protection

```python
from piesharkx.security import generate_csrf_token, validate_csrf_token

@app.before_request
def csrf_protect():
    if request.method in ['POST', 'PUT', 'DELETE']:
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(token):
            return app.abort(403, "CSRF token missing or invalid")

@app.route('/form')
async def show_form():
    csrf_token = generate_csrf_token()
    return Templates("""
        <form method="post" action="/submit">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="text" name="data" required>
            <button type="submit">Submit</button>
        </form>
    """, csrf_token=csrf_token)
```

### Input Validation & Sanitization

```python
import html
import re
from urllib.parse import quote

def sanitize_input(data):
    """Sanitize user input"""
    if isinstance(data, str):
        # HTML escape
        data = html.escape(data)
        # Remove potentially dangerous characters
        data = re.sub(r'[<>"\']', '', data)
    return data

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/register', methods=['POST'])
async def register():
    username = sanitize_input(form.username.decode())
    email = form.email.decode()
    password = form.password.decode()
    
    # Validation
    if not username or len(username) < 3:
        return app.json_response({"error": "Username too short"}, status=400)
    
    if not validate_email(email):
        return app.json_response({"error": "Invalid email"}, status=400)
    
    if len(password) < 8:
        return app.json_response({"error": "Password too short"}, status=400)
    
    # Hash password before storing
    hashed_password = hash_password(password)
    
    # Create user logic
    return app.json_response({"status": "user created"})
```

### Rate Limiting

```python
from collections import defaultdict
from time import time

# Simple in-memory rate limiter
rate_limit_storage = defaultdict(list)

def rate_limit(max_requests=100, window=3600):  # 100 requests per hour
    def decorator(func):
        async def wrapper(*args, **kwargs):
            client_ip = request.environ.get('REMOTE_ADDR')
            now = time()
            
            # Clean old entries
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage[client_ip]
                if now - req_time < window
            ]
            
            # Check rate limit
            if len(rate_limit_storage[client_ip]) >= max_requests:
                return app.json_response(
                    {"error": "Rate limit exceeded"}, 
                    status=429
                )
            
            # Add current request
            rate_limit_storage[client_ip].append(now)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/api/data')
@rate_limit(max_requests=10, window=60)  # 10 requests per minute
async def get_data():
    return app.json_response({"data": "protected endpoint"})
```

### Security Headers

```python
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

---

## 📁 Static Files

PieSharkX menyediakan sistem static file serving yang efisien.

### Basic Static Files

```python
# Serve static files
app.static("static/", "/static/")
app.static("uploads/", "/files/")
app.static("assets/", "/assets/")

# File akan dapat diakses di:
# /static/style.css -> static/style.css
# /files/document.pdf -> uploads/document.pdf
# /assets/logo.png -> assets/logo.png
```

### Advanced Static Configuration

```python
# Konfigurasi static files dengan cache headers
@app.route('/static/{path:path}')
async def serve_static(path):
    response = app.send_static_file('static/' + path)
    
    # Add cache headers for better performance
    if path.endswith(('.css', '.js', '.png', '.jpg', '.gif')):
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day
    
    return response

# Serve files dengan content type detection
import mimetypes

@app.route('/media/{filename}')
async def serve_media(filename):
    file_path = f"media/{filename}"
    
    if not os.path.exists(file_path):
        return app.abort(404)
    
    content_type, _ = mimetypes.guess_type(file_path)
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    response = app.make_response(content)
    response.headers['Content-Type'] = content_type or 'application/octet-stream'
    
    return response
```

### CDN Integration

```python
from piesharkx.pydejs import PY_deJS

# CDN resource fetcher
deJS = PY_deJS()
deJS.get(search=['jquery', 'bootstrap'], limit=5)
deJS.select(['min', 'css'])

@app.route("/")
async def home():
    # Fetch jQuery from CDN
    jquery_results = deJS.get(search="jquery", limit=1)
    jquery_url = deJS.select("min")
    
    # Fetch Bootstrap
    bootstrap_results = deJS.get(search="bootstrap", limit=1)
    bootstrap_css = deJS.select("css")
    bootstrap_js = deJS.select("js")
    
    return Templates("""
        <!DOCTYPE html>
        <html>
        <head>
            <link href="{{ bootstrap_css }}" rel="stylesheet">
        </head>
        <body>
            <div class="container">
                <h1>PieSharkX with CDN Resources</h1>
            </div>
            <script src="{{ jquery_url }}"></script>
            <script src="{{ bootstrap_js }}"></script>
        </body>
        </html>
    """, 
    jquery_url=deJS.scripts_safe.jquery,
    bootstrap_css=bootstrap_css,
    bootstrap_js=bootstrap_js
    )
```

---

## 📤 Form Processing & File Upload

### Basic Form Processing

```python
@app.route("/contact", methods=["GET", "POST"])
async def contact():
    if request.method == "POST":
        # Form data otomatis terenkripsi
        name = form.name.decode()
        email = form.email.decode()
        message = form.message.decode()
        fileupload = form.filesupload
        # Validation
        if not name or not email or not message:
            return Templates("contact.shark", 
                           error="All fields are required")
        
        # Process form (send email, save to database, etc.)
        send_contact_email(name, email, message)
        
        return Templates("contact.shark", 
                        success="Message sent successfully!")
    
    return Templates("""
        <form method="post">
            <div>
                <label>Name:</label>
                <input type="text" name="name" required>
            </div>
            <div>
                <label>Email:</label>
                <input type="email" name="email" required>
            </div>
            <div>
                <label>Email:</label>
                <input type="file" name="fileupload">
            </div>
            <div>
                <label>Message:</label>
                <textarea name="message" required></textarea>
            </div>
            <button type="submit">Send Message</button>
        </form>
    """)
```

---

## 🔄 Middleware & Hooks

PieSharkX menyediakan sistem middleware dan hooks yang fleksibel.

### Request Lifecycle Hooks

```python
@app.before_request
def before_request():
    """Dijalankan sebelum setiap request"""
    # Logging request
    print(f"Request: {request.method} {request.path}")
    
    # Authentication check
    if request.path.startswith('/admin/'):
        if not session.get('is_admin'):
            return app.abort(403)
    
    # Rate limiting
    client_ip = request.environ.get('REMOTE_ADDR')
    if is_rate_limited(client_ip):
        return app.json_response({"error": "Rate limit exceeded"}, status=429)

@app.after_request
def after_request(response):
    """Dijalankan setelah setiap request"""
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    
    # CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
    
    # Logging response
    print(f"Response: {response.status_code}")
    
    return response
```

### Error Handling Middleware

```python
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return app.json_response({"error": "Endpoint not found"}, status=404)
    return Templates("errors/404.shark"), 404

@app.errorhandler(500)
def internal_error(error):
    # Log the error
    print(f"Internal error: {error}")
    
    if request.path.startswith('/api/'):
        return app.json_response({"error": "Internal server error"}, status=500)
    return Templates("errors/500.shark"), 500

@app.errorhandler(403)
def forbidden(error):
    return app.json_response({"error": "Access forbidden"}, status=403)

# Custom exception handling
class ValidationError(Exception):
    pass

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return app.json_response({"error": str(error)}, status=400)
```

---

## 🌐 API Development

PieSharkX sangat cocok untuk pengembangan API modern.

### RESTful API Structure

```python
# blueprints/api_v1.py
from piesharkx.blueprint import Blueprint

api_v1 = Blueprint('api_v1', url_prefix='/api/v1')

# Users endpoint
@api_v1.route('/users', methods=['GET'])
async def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    users, total = get_users_paginated(page, per_page, search)
    
    return app.json_response({
        "users": users,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        },
        "meta": {
            "search": search,
            "count": len(users)
        }
    })

@api_v1.route('/users', methods=['POST'])
async def create_user():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return app.json_response({
                    "error": f"Missing required field: {field}"
                }, status=400)
        
        # Create user
        new_user = create_user_service(data)
        
        return app.json_response({
            "user": new_user,
            "message": "User created successfully"
        }, status=201)
        
    except ValidationError as e:
        return app.json_response({"error": str(e)}, status=400)
    except Exception as e:
        return app.json_response({"error": "Internal server error"}, status=500)

@api_v1.route('/users/{user_id}', methods=['GET'])
async def get_user(user_id):
    user = get_user_by_id(user_id)
    
    if not user:
        return app.json_response({"error": "User not found"}, status=404)
    
    return app.json_response({"user": user})

@api_v1.route('/users/{user_id}', methods=['PUT'])
async def update_user(user_id):
    try:
        data = request.get_json()
        updated_user = update_user_service(user_id, data)
        
        if not updated_user:
            return app.json_response({"error": "User not found"}, status=404)
        
        return app.json_response({
            "user": updated_user,
            "message": "User updated successfully"
        })
        
    except ValidationError as e:
        return app.json_response({"error": str(e)}, status=400)

@api_v1.route('/users/{user_id}', methods=['DELETE'])
async def delete_user(user_id):
    if delete_user_service(user_id):
        return app.json_response({"message": "User deleted successfully"})
    else:
        return app.json_response({"error": "User not found"}, status=404)
```

### API Authentication

```python
import jwt
from functools import wraps

def jwt_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return app.json_response({"error": "Token missing"}, status=401)
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            payload = jwt.decode(token, app.config['secret_key'], algorithms=['HS256'])
            request.user_id = payload['user_id']
            request.username = payload['username']
        except jwt.ExpiredSignatureError:
            return app.json_response({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return app.json_response({"error": "Invalid token"}, status=401)
        
        return await f(*args, **kwargs)
    return decorated_function

@api_v1.route('/auth/login', methods=['POST'])
async def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = authenticate_user(username, password)
    
    if user:
        payload = {
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, app.config['secret_key'], algorithm='HS256')
        
        return app.json_response({
            "token": token,
            "user": user,
            "expires_in": 86400  # 24 hours
        })
    else:
        return app.json_response({"error": "Invalid credentials"}, status=401)

@api_v1.route('/auth/profile', methods=['GET'])
@jwt_required
async def get_profile():
    user = get_user_by_id(request.user_id)
    return app.json_response({"user": user})
```

### API Documentation

```python
@api_v1.route('/docs')
async def api_docs():
    docs = {
        "title": "PieSharkX API Documentation",
        "version": "1.0.0",
        "base_url": "/api/v1",
        "endpoints": {
            "auth": {
                "POST /auth/login": {
                    "description": "Authenticate user and get JWT token",
                    "parameters": {
                        "username": "string (required)",
                        "password": "string (required)"
                    },
                    "response": {
                        "token": "JWT token string",
                        "user": "User object",
                        "expires_in": "Token expiry in seconds"
                    }
                },
                "GET /auth/profile": {
                    "description": "Get current user profile",
                    "headers": {
                        "Authorization": "Bearer <token>"
                    },
                    "response": {
                        "user": "User object"
                    }
                }
            },
            "users": {
                "GET /users": {
                    "description": "List users with pagination",
                    "parameters": {
                        "page": "integer (optional, default: 1)",
                        "per_page": "integer (optional, default: 10)",
                        "search": "string (optional)"
                    }
                },
                "POST /users": {
                    "description": "Create new user",
                    "parameters": {
                        "username": "string (required)",
                        "email": "string (required)",
                        "password": "string (required)"
                    }
                },
                "GET /users/{id}": {
                    "description": "Get user by ID"
                },
                "PUT /users/{id}": {
                    "description": "Update user by ID"
                },
                "DELETE /users/{id}": {
                    "description": "Delete user by ID"
                }
            }
        }
    }
    
    return app.json_response(docs)
```

---

## 🛠️ CLI Tools

PieSharkX menyediakan command line interface yang powerful untuk development.

### Perintah Dasar CLI

```bash
# Install CLI tools
pip install click watchdog

# Menjalankan aplikasi
pieshark run

# Dengan opsi development
pieshark run --debug --reload --host 0.0.0.0 --port 8000

# Melihat semua routes
pieshark routes

# Shell interaktif
pieshark shell

# Membuat proyek baru
pieshark init myproject --template full

# Pengecekan aplikasi
pieshark check
```