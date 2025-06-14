# 🦈 PieShark Framework
*A Lightweight, Powerful Python Web Framework*

---

## 🚀 Overview

**PieShark** is a modern, lightweight WSGI-based Python web framework designed for developers who want power without complexity. Built with performance and security in mind, it offers everything you need to create robust web applications and APIs.

### ✨ Key Features

- 🛣️ **Flexible Routing** - Path parameters, regex patterns, and RESTful endpoints
- 🔐 **Built-in Security** - Automatic session and cookie encryption
- 🧩 **Modular Design** - Blueprint system for organized code architecture
- ⚡ **Async/Sync Support** - Native support for both synchronous and asynchronous handlers
- 🎨 **Simple Templating** - Lightweight template engine with Python variable injection
- 🔧 **Middleware Ready** - Custom middleware support for request/response processing
- 📦 **Static File Serving** - Built-in static file handling

---

## 🏁 Quick Start

### Installation & Setup

```python
from PieShark.main import pieshark, request, form, session
from PieShark.blueprint import Blueprint
from PieShark.session import SESSION
from PieShark.cookie import Cookie
from PieShark.templates import Templates
from PieShark.pydejs import PY_deJS

# Initialize your application
app = pieshark(debug=True)

# Configure your app
app.config.update({
    'secret_key': 'your-super-secret-key-here',
    'session_permanent': True,
    'url_dbase': 'base://sqlite3:static',
    'limit_size_upload': 3089003  # ~3MB upload limit
})
```

### Your First Route

```python
@app.route("/")
async def home():
    session['user'] = 'Developer'
    return Templates(
        "<h1>Welcome to {{ framework }}!</h1>", 
        framework="PieShark"
    )

@app.route("/api/user/{user_id}")
async def get_user(user_id):
    return app.json_response({
        "user_id": user_id,
        "status": "active"
    })
```

---

## 🛣️ Advanced Routing

PieShark supports multiple routing patterns to fit your application's needs:

### Dynamic Parameters
```python
@app.route("/users/{user_id}/posts/{post_id}")
async def get_user_post(user_id, post_id):
    return f"User {user_id}, Post {post_id}"
```

### HTTP Methods
```python
@app.route("/api/data", methods=["GET", "POST", "PUT", "DELETE"])
async def handle_data():
    if request.method == "POST":
        # Handle POST data
        return app.json_response({"created": True})
    elif request.method == "GET":
        # Handle GET request
        return app.json_response({"data": "sample"})
```

---

## 🔐 Security Features

### Session Management
```python
@app.route("/login", methods=["POST"])
async def login():
    # Sessions are automatically encrypted
    session['user_id'] = 12345
    session['username'] = 'john_doe'
    session['roles'] = ['user', 'admin']
    return app.redirect("/dashboard")

@app.route("/dashboard")
async def dashboard():
    if not session.get('user_id'):
        return app.abort(401)
    return f"Welcome back, {session['username']}!"
```

### Encrypted Cookies
```python
# Initialize cookie handler with custom salt
cookie = Cookie(salt="your_custom_salt", app=app)

@app.route("/set-preference")
async def set_preference():
    # Cookies are automatically encrypted
    cookie.create("theme=dark&lang=en")
    return "Preferences saved!"

@app.route("/get-preference")
async def get_preference():
    # Decrypt and read cookie data
    theme = cookie.select.theme.decode()
    return f"Current theme: {theme}"
```

---

## 🧩 Modular Architecture with Blueprints

Organize your application into logical modules:

```python
# auth_blueprint.py
auth_bp = Blueprint('auth', url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        username = form.username.decode()
        password = form.password.decode()
        
        # Your authentication logic here
        if authenticate(username, password):
            session['user'] = username
            return app.redirect('/dashboard')
    
    return Templates("""
        <form method="post">
            <input name="username" type="text" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    """)

@auth_bp.route('/logout')
async def logout():
    session.clear()
    return app.redirect('/')

# Register blueprint in main app
app.register_blueprint(auth_bp)
```

---

## 🎨 Template System

### Inline Templates
```python
@app.route("/profile/{username}")
async def profile(username):
    user_data = get_user_data(username)  # Your data fetching logic
    
    return Templates("""
        <div class="profile">
            <h1>{{ user.name }}</h1>
            <p>Email: {{ user.email }}</p>
            <p>Joined: {{ user.join_date }}</p>
        </div>
    """, user=user_data)
```

### File-based Templates
```python
# For larger templates, use external files
@app.route("/complex-page")
async def complex_page():
    return Templates("complex_template.shark", 
                    title="My App",
                    data=fetch_page_data())
```

---

## 📁 Static File Handling

```python
# Serve static files
app.static("static/", "/static/")
app.static("uploads/", "/files/")

# Now accessible at:
# /static/style.css -> static/style.css
# /files/document.pdf -> uploads/document.pdf
```

---

## 📤 Form Processing & File Uploads

```python
@app.route("/upload", methods=["GET", "POST"])
async def upload_file():
    if request.method == "POST":
        # Access form data (automatically encrypted)
        title = form.title.decode()
        description = form.description.decode()
        
        # Handle file uploads
        uploaded_file = form.file  # File object
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            ///Logic your saving file
        
        return app.json_response({
            "status": "success",
            "title": title,
            "filename": filename
        })
    
    return Templates("""
        <form method="post" enctype="multipart/form-data">
            <input name="title" type="text" placeholder="Title" required>
            <textarea name="description" placeholder="Description"></textarea>
            <input name="file" type="file" required>
            <button type="submit">Upload</button>
        </form>
    """)
```

---

## 🔄 Middleware & Hooks

### Request Lifecycle Hooks
```python
@app.before_request
def authenticate_user():
    """Run before every request"""
    if request.path.startswith('/admin/'):
        if not session.get('is_admin'):
            return app.abort(403)

@app.after_request
def add_security_headers(response):
    """Run after every request"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
```

### Custom Middleware
```python
class RequestTimingMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        start_time = time.time()
        response = self.app(environ, start_response)
        end_time = time.time()
        
        print(f"Request took {end_time - start_time:.2f}s")
        return response

# Apply middleware
app.wsgi_app = RequestTimingMiddleware(app.wsgi_app)
```

---

## 🌐 API Development

### RESTful API Example
```python
api_bp = Blueprint('api', url_prefix='/api/v1')

@api_bp.route('/users', methods=['GET'])
async def list_users():
    users = get_all_users()  # Your data logic
    return app.json_response({
        "users": users,
        "count": len(users)
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
        delete_user(user_id)
        return app.json_response({"message": "User deleted"})

app.register_blueprint(api_bp)
```

---

## 🛠️ Utilities & Helpers

### CDN Resource Fetcher (PyDeJS)
```python
deJS = PY_deJS()

# Search for JavaScript libraries
jquery_results = deJS.get(search="jquery", limit=1)
minified_jquery = deJS.select("min")

# Use in templates
@app.route("/")
async def home():
    return Templates("""
        <script src="{{ jquery_url }}"></script>
        <h1>jQuery Loaded!</h1>
    """, jquery_url=minified_jquery)
```

---

## 🚀 Deployment

### Development Server
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```

### Production Deployment

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### Using Waitress
```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

### Nginx Configuration Example
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static/ {
        alias /path/to/your/static/files/;
        expires 30d;
    }
}
```

---

## 📋 Best Practices

### Project Structure
```
your_project/
│
├── app.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
│
├── blueprints/            # Application modules
│   ├── __init__.py
│   ├── auth.py
│   ├── api.py
│   └── admin.py
│
├── static/                # Static assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/             # Template files
│   ├── base.shark
│   ├── home.shark
│   └── auth/
│       ├── login.shark
│       └── register.shark
│
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── auth.py
│   └── helpers.py
│
└── tests/                 # Test files
    ├── __init__.py
    ├── test_auth.py
    └── test_api.py
```

### Security Checklist
- ✅ Use strong, unique `secret_key`
- ✅ Store sensitive config in environment variables
- ✅ Validate all user inputs
- ✅ Use HTTPS in production
- ✅ Implement proper error handling
- ✅ Set appropriate file upload limits
- ✅ Regular security updates

### Performance Tips
- Use async handlers for I/O-bound operations
- Implement caching for frequently accessed data
- Optimize database queries
- Use CDN for static assets
- Enable gzip compression
- Monitor application performance

---

## 🤝 Contributing

PieShark is designed to be lightweight yet powerful. Whether you're building a simple API, a complex web application, or a microservice, PieShark provides the tools you need without the bloat.

### Why Choose PieShark?

| Feature | PieShark | Other Frameworks |
|---------|----------|------------------|
| **Learning Curve** | Minimal | Steep |
| **Built-in Security** | ✅ Encrypted sessions/cookies | ❌ Manual setup |
| **Async Support** | ✅ Native | ⚠️ Plugin required |
| **File Size** | Lightweight | Heavy |
| **Flexibility** | High | Medium |

---

## 📚 Next Steps

1. **Start Small** - Begin with a simple route and gradually add features
2. **Explore Blueprints** - Organize your code into logical modules
3. **Implement Security** - Leverage built-in encryption and session management
4. **Scale Up** - Use async handlers and proper deployment strategies
5. **Contribute** - Help make PieShark even better

---

*Ready to dive in? Start building your next web application with PieShark today! 🦈⚡*