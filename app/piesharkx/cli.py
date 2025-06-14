#!/usr/bin/env python3
"""
PieShark CLI Tool
Similar to Flask CLI for running and managing PieShark applications
"""

import os
import sys
import click
import importlib.util
import inspect
from pathlib import Path
import subprocess
import threading
import time
import signal
from datetime import datetime

__all__ = ["cli"]
# Add current directory to Python path
sys.path.insert(0, os.getcwd())

class PieSharkCLI:
    def __init__(self):
        self.app = None
        self.app_file = None
        self.debug = False
        
    def find_app_file(self):
        """Find the main application file"""
        possible_files = ['app.py', 'main.py', 'application.py', 'run.py']
        
        for filename in possible_files:
            if os.path.exists(filename):
                return filename
        
        # Look for any Python file containing pieshark app
        for file in os.listdir('.'):
            if file.endswith('.py'):
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if 'pieshark' in content.lower() and ('app' in content or 'application' in content):
                            return file
                except:
                    continue
        
        return None
    
    def load_app(self, app_file=None):
        """Load the PieShark application from file"""
        if not app_file:
            app_file = self.find_app_file()
        
        if not app_file:
            click.echo("Error: Could not find application file. Expected: app.py, main.py, application.py, or run.py")
            sys.exit(1)
        
        if not os.path.exists(app_file):
            click.echo(f"Error: Application file '{app_file}' not found")
            sys.exit(1)
        
        self.app_file = app_file
        
        # Load the module
        spec = importlib.util.spec_from_file_location("app_module", app_file)
        app_module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(app_module)
        except Exception as e:
            click.echo(f"Error loading application: {e}")
            sys.exit(1)
        
        # Find the pieshark app instance
        app_instance = None
        for name, obj in inspect.getmembers(app_module):
            if hasattr(obj, '__class__') and 'pieshark' in str(type(obj)).lower():
                app_instance = obj
                break
        
        if not app_instance:
            click.echo("Error: No PieShark application instance found")
            sys.exit(1)
        
        self.app = app_instance
        return app_instance
    
    def get_routes_info(self):
        """Get information about registered routes"""
        if not self.app:
            return []
        
        routes_info = []
        
        # Regular routes
        for path, (handler, methods) in self.app.routes.items():
            routes_info.append({
                'path': path,
                'methods': methods,
                'handler': handler.__name__ if hasattr(handler, '__name__') else str(handler),
                'type': 'route'
            })
        
        # Regex routes
        for pattern, (handler, methods) in self.app.route_patterns.items():
            routes_info.append({
                'path': pattern.pattern,
                'methods': methods,
                'handler': handler.__name__ if hasattr(handler, '__name__') else str(handler),
                'type': 'regex'
            })
        
        return routes_info

cli_instance = PieSharkCLI()

@click.group()
@click.option('--app', '-a', help='Application file to load')
@click.option('--debug/--no-debug', default=False, help='Enable debug mode')
def cli(app, debug):
    """PieShark CLI - Command line interface for PieShark applications"""
    cli_instance.debug = debug
    if app:
        cli_instance.load_app(app)

@cli.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
@click.option('--port', '-p', default=5000, type=int, help='Port to bind to')
@click.option('--debug/--no-debug', default=None, help='Enable debug mode')
@click.option('--reload/--no-reload', default=False, help='Enable auto-reload on file changes')
@click.option('--ssl-cert', help='SSL certificate file')
@click.option('--ssl-key', help='SSL private key file')
def run(host, port, debug, reload, ssl_cert, ssl_key):
    """Run the PieShark application"""
    
    app = cli_instance.load_app()
    
    # Set debug mode
    if debug is not None:
        app.debug = debug
        cli_instance.debug = debug
    elif cli_instance.debug:
        app.debug = True
    
    # SSL context
    ssl_context = None
    if ssl_cert and ssl_key:
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_cert, ssl_key)
        click.echo(f"SSL enabled with cert: {ssl_cert}")
    
    click.echo(f"Starting PieShark application...")
    click.echo(f"App file: {cli_instance.app_file}")
    click.echo(f"Debug mode: {app.debug}")
    click.echo(f"Running on {'https' if ssl_context else 'http'}://{host}:{port}")
    
    if reload and not ssl_context:
        run_with_reload(app, host, port, ssl_context)
    else:
        if reload and ssl_context:
            click.echo("Warning: Auto-reload not supported with SSL")
        
        try:
            app.run(host=host, port=port, ssl_context=ssl_context)
        except KeyboardInterrupt:
            click.echo("\nShutting down...")
        except Exception as e:
            click.echo(f"Error: {e}")
            sys.exit(1)

@cli.command()
def routes():
    """Show all registered routes"""
    
    app = cli_instance.load_app()
    routes_info = cli_instance.get_routes_info()
    
    if not routes_info:
        click.echo("No routes registered")
        return
    
    click.echo("Registered Routes:")
    click.echo("-" * 80)
    
    # Header
    click.echo(f"{'Path':<30} {'Methods':<15} {'Handler':<20} {'Type':<10}")
    click.echo("-" * 80)
    
    for route in routes_info:
        methods_str = ', '.join(route['methods'])
        click.echo(f"{route['path']:<30} {methods_str:<15} {route['handler']:<20} {route['type']:<10}")

@cli.command()
def shell():
    """Start an interactive shell with app context"""
    
    app = cli_instance.load_app()
    
    try:
        import IPython
        banner = f"PieShark Shell\nApp: {cli_instance.app_file}\nApp object available as 'app'"
        IPython.embed(banner1=banner, user_ns={'app': app})
    except ImportError:
        import code
        banner = f"PieShark Shell\nApp: {cli_instance.app_file}\nApp object available as 'app'"
        code.interact(banner=banner, local={'app': app})

@cli.command()
@click.argument('name')
@click.option('--template', default='basic', help='Template to use (basic, api, full)')
def init(name, template):
    """Initialize a new PieShark project"""
    
    if os.path.exists(name):
        click.echo(f"Error: Directory '{name}' already exists")
        sys.exit(1)
    
    os.makedirs(name)
    os.chdir(name)
    
    templates = {
        'basic': create_basic_template,
        'api': create_api_template,
        'full': create_full_template
    }
    
    if template not in templates:
        click.echo(f"Error: Unknown template '{template}'. Available: {', '.join(templates.keys())}")
        sys.exit(1)
    
    templates[template](name)
    click.echo(f"Created PieShark project '{name}' using '{template}' template")
    click.echo(f"To run: pieshark run")

@cli.command()
def check():
    """Check application for common issues"""
    
    app = cli_instance.load_app()
    
    click.echo("Checking PieShark application...")
    issues = []
    
    # Check if secret key is set
    if not hasattr(app, 'secret_key') or not app.secret_key:
        issues.append("Warning: No secret key set")
    
    # Check if debug mode is enabled in production
    if app.debug:
        issues.append("Warning: Debug mode is enabled")
    
    # Check for duplicate routes
    routes = cli_instance.get_routes_info()
    paths = [r['path'] for r in routes]
    duplicates = set([p for p in paths if paths.count(p) > 1])
    if duplicates:
        issues.append(f"Warning: Duplicate routes found: {', '.join(duplicates)}")
    
    # Check if static files are configured
    if not hasattr(app, 'static_file') or not app.static_file:
        issues.append("Info: No static files configured")
    
    if issues:
        click.echo("Issues found:")
        for issue in issues:
            click.echo(f"  - {issue}")
    else:
        click.echo("No issues found!")
    
    click.echo(f"Total routes: {len(routes)}")
    click.echo(f"Debug mode: {app.debug}")

def run_with_reload(app, host, port, ssl_context):
    """Run app with auto-reload functionality"""
    
    def watch_files():
        """Watch for file changes"""
        import time
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class ReloadHandler(FileSystemEventHandler):
            def __init__(self):
                self.last_modified = time.time()
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                if event.src_path.endswith('.py'):
                    current_time = time.time()
                    if current_time - self.last_modified > 1:  # Debounce
                        self.last_modified = current_time
                        click.echo(f"File changed: {event.src_path}")
                        click.echo("Restarting...")
                        os.execv(sys.executable, [sys.executable] + sys.argv)
        
        observer = Observer()
        observer.schedule(ReloadHandler(), path='.', recursive=True)
        observer.start()
        
        try:
            app.run(host=host, port=port, ssl_context=ssl_context)
        except KeyboardInterrupt:
            observer.stop()
            click.echo("\nShutting down...")
        
        observer.join()
    
    try:
        from watchdog.observers import Observer
        watch_files()
    except ImportError:
        click.echo("Warning: watchdog not installed. Auto-reload disabled.")
        click.echo("Install with: pip install watchdog")
        app.run(host=host, port=port, ssl_context=ssl_context)

def create_basic_template(name):
    """Create basic project template"""
    
    # app.py
    with open('app.py', 'w') as f:
        f.write(f'''from piesharkx import pieshark

app = pieshark(debug=True)

@app.route('/')
def index():
    return "Hello from {name}!"

@app.route('/about')
def about():
    return "About {name}"

if __name__ == '__main__':
    app.run()
''')
    
    # requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write('piesharkx\n')
    
    # README.md
    with open('README.md', 'w') as f:
        f.write(f'''# {name}

A PieShark application.

## Running

```bash
pieshark run
```

## Development

```bash
pieshark run --debug --reload
```
''')

def create_api_template(name):
    """Create API project template"""
    
    with open('app.py', 'w') as f:
        f.write(f'''from piesharkx import pieshark

app = pieshark(debug=True)

@app.route('/api/health')
def health():
    return {{"status": "ok", "service": "{name}"}}

@app.route('/api/users', methods=['GET'])
def get_users():
    return {{"users": []}}

@app.route('/api/users', methods=['POST'])
def create_user():
    return {{"message": "User created"}}, 201

if __name__ == '__main__':
    app.run()
''')
    
    with open('requirements.txt', 'w') as f:
        f.write('piesharkx\n')

def create_full_template(name):
    """Create full project template with structure"""
    
    # Create directories
    os.makedirs('templates')
    os.makedirs('static/css')
    os.makedirs('static/js')
    
    # app.py
    with open('app.py', 'w') as f:
        f.write(f'''from piesharkx import pieshark

app = pieshark(debug=True)

# Configure static files
app.static('static')

@app.route('/')
def index():
    return "Welcome to {name}!"

@app.route('/api/status')
def api_status():
    return {{"status": "running", "app": "{name}"}}

@app.before_request
def before_request():
    print("Before request hook")

@app.after_request
def after_request(response):
    print("After request hook")
    return response

if __name__ == '__main__':
    app.run()
''')
    
    # Static files
    with open('static/css/style.css', 'w') as f:
        f.write('/* Add your styles here */')
    
    with open('static/js/app.js', 'w') as f:
        f.write('// Add your JavaScript here')
    
    # Config file
    with open('config.py', 'w') as f:
        f.write(f'''class Config:
    SECRET_KEY = 'your-secret-key-here'
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
''')
    
    with open('requirements.txt', 'w') as f:
        f.write('piesharkx\nwatchdog\n')

if __name__ == '__main__':
    cli()