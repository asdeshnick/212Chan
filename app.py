from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import argparse

# Parse command line arguments for port
parser = argparse.ArgumentParser(description='Run Flask app with Flask-Login')
parser.add_argument('--port', type=int, default=7000, help='Port to run the Flask app on (default: 8000)')
args = parser.parse_args()

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random secret key in production

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Note: this is the endpoint name, not the URL path
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
login_manager.login_message_category = "error"

# Simple user model
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Simulate a user database
users = {}
# Add a test user
users[1] = User(1, 'admin', 'password123')

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Find user by username (in a real app, you'd query a database)
        user = next((u for u in users.values() if u.username == username), None)

        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')

            # Get the next page from the request args, or default to dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# Create basic templates for testing
@app.route('/create_templates')
def create_templates():
    import os

    if not os.path.exists('templates'):
        os.makedirs('templates')

    templates = {
        'home.html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Home</title>
            </head>
            <body>
                <h1>Welcome to the Flask-Login Test</h1>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        <ul class="flashes">
                            {% for category, message in messages %}
                                <li class="{{ category }}">{{ message }}</li>
                            {% endfor %}
                        </ul>
                    {% endif %}
                {% endwith %}
                <p><a href="{{ url_for('login') }}">Login</a></p>
                <p><a href="{{ url_for('dashboard') }}">Dashboard (Protected)</a></p>
            </body>
            </html>
        ''',
        'login.html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login</title>
            </head>
            <body>
                <h1>Login</h1>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        <ul class="flashes">
                            {% for category, message in messages %}
                                <li class="{{ category }}">{{ message }}</li>
                            {% endfor %}
                        </ul>
                    {% endif %}
                {% endwith %}
                <form method="POST">
                    <div>
                        <label>Username:</label>
                        <input type="text" name="username" required>
                    </div>
                    <div>
                        <label>Password:</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
                <p><a href="{{ url_for('home') }}">Back to Home</a></p>
            </body>
            </html>
        ''',
        'dashboard.html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard</title>
            </head>
            <body>
                <h1>Dashboard</h1>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        <ul class="flashes">
                            {% for category, message in messages %}
                                <li class="{{ category }}">{{ message }}</li>
                            {% endfor %}
                        </ul>
                    {% endif %}
                {% endwith %}
                <p>Welcome, {{ current_user.username }}!</p>
                <p>This is a protected page that only logged-in users can see.</p>
                <p><a href="{{ url_for('profile') }}">View Profile</a></p>
                <p><a href="{{ url_for('logout') }}">Logout</a></p>
            </body>
            </html>
        ''',
        'profile.html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Profile</title>
            </head>
            <body>
                <h1>User Profile</h1>
                <p>User ID: {{ current_user.id }}</p>
                <p>Username: {{ current_user.username }}</p>
                <p><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></p>
                <p><a href="{{ url_for('logout') }}">Logout</a></p>
            </body>
            </html>
        '''
    }

    for filename, content in templates.items():
        with open(os.path.join('templates', filename), 'w') as f:
            f.write(content)

    return "Templates created! You can now use the application."

if __name__ == '__main__':
    port = args.port
    print(f"Starting Flask app on port {port}...")
    app.run(debug=True, host='0.0.0.0', port=8000)
