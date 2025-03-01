from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, request, redirect, render_template, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_misaka import Misaka
from flask_wtf import FlaskForm
from datetime import datetime
from database import db
from util import *
import sqlite3
import config

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
# socketio = SocketIO(app, async_mode="threading")

with app.app_context():
    db.create_all()

Misaka(app=app, escape=True, no_images=True,
       wrap=True, autolink=True, no_intra_emphasis=True,
       space_headers=True)


# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Страница входа
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
login_manager.login_message_category = "error"

# Модель пользователя
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Пример базы данных пользователей
users = {
    1: User(1, 'admin', generate_password_hash('password'))  # Хеширование пароля
}

# Загрузчик пользователя
@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Маршрут для входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = next((user for user in users.values() if user.username == username), None)
        if user and user.check_password(password):
            login_user(user)  # Сохраняем пользователя в сессии
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('admin_boards'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html')

# Защищенный маршрут
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return "Welcome to the Admin Dashboard!"

# Отключаем кэширование
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


@app.route('/')
def show_frontpage():
    # Получение IP-адреса пользователя
    ip_address = request.remote_addr
    print(ip_address)
    # Получение User-Agent пользователя
    user_agent = request.headers.get('User-Agent')
    print(user_agent)
    save_visitor(ip_address, user_agent)
    
    return render_template('home.html'), "Hello World!"

# Маршрут для чека пользователей
@app.route('/visitors')
def show_visitors():
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('SELECT * FROM visitors')
    visitors = c.fetchall()
    conn.close()
    return render_template('index.html', visitors=visitors)

# Маршрут для ALL
@app.route('/all/')
def show_all():
    OPs = get_OPs_all()
    entry_list = []
    for OP in OPs:
        replies = get_last_replies(OP.id)
        entry_list.append(OP)
        entry_list += replies[::-1]
    return render_template('show_all.html', entries=entry_list, board='all')

@app.route('/<board>/')
def show_board(board):
    if board_inexistent(board):
        return redirect('/')
    OPs = get_OPs(board)
    entry_list = []
    for OP in OPs:
        replies = get_last_replies(OP.id)
        entry_list.append(OP)
        entry_list += replies[::-1]

    sidebar = get_sidebar(board)

    return render_template('show_board.html', entries=entry_list, board=board, sidebar=sidebar, id=0)

@app.route('/<board>/catalog')
def show_catalog(board):
    OPs = get_OPs_catalog(board)
    sidebar = get_sidebar(board)

    return render_template('show_catalog.html', entries=OPs, board=board, sidebar=sidebar)

@app.route('/<board>/<id>/')
def show_thread(board, id):
    OP = get_thread_OP(id)
    replies = get_replies(id)
    sidebar = get_sidebar(board)

    return render_template('show_thread.html', entries=OP + replies, board=board, id=id, sidebar=sidebar)

@app.route('/add', methods=['POST'])
def new_thread():
    board = request.form['board']
    if no_image():
        return redirect('/' + board + '/')

    newPost = new_post(board)
    newPost.last_bump = datetime.now()
    db.session.add(newPost)
    db.session.commit()
    return redirect('/' + board + '/')

@app.route('/add_reply', methods=['POST'])
def add_reply():
    board = request.form['board']
    thread = request.form['op_id']
    print(thread, board)
    if no_content_or_image():
        return redirect('/' + board + '/')

    newPost = new_post(board, thread)
    db.session.add(newPost)
    if reply_count(thread) < BUMP_LIMIT:
        bump_thread(thread)
    db.session.commit()
    return redirect('/' + board + '/') #+ thread)


@app.route('/admin/boards')
@login_required
def admin_boards():
    boards = db.session.query(Boards).all()
    return render_template('admin_boards.html', boards=boards)

@app.route('/admin/boards/create', methods=['GET', 'POST'])
@login_required
def admin_create_board():
    if request.method == 'POST':
        return create_board()
    return render_template('admin_create_board.html')

@app.route('/admin/boards/edit/<name>', methods=['GET', 'POST'])
@login_required
def admin_edit_board(name):
    if request.method == 'POST':
        return edit_board(name)
    board = db.session.query(Boards).filter_by(name=name).first()
    return render_template('admin_edit_board.html', board=board)

@app.route('/admin/boards/delete/<name>', methods=['POST'])
@login_required
def admin_delete_board(name):
    return delete_board(name)

@app.route('/admin/posts')
@login_required
def admin_posts():
    posts = db.session.query(Posts).order_by(Posts.date.desc()).all()
    return render_template('admin_posts.html', posts=posts)

@app.route('/admin/posts/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_post(id):
    return delete_post(id)

@app.route('/admin/posts/restore/<int:id>', methods=['POST'])
@login_required
def admin_restore_post(id):
    return restore_post(id)

@app.route('/admin/posts/permanently_delete/<int:id>', methods=['POST'])
@login_required
def admin_permanently_delete_post(id):
    return permanently_delete_post(id)

@app.route('/admin/posts/delete_image/<int:id>', methods=['POST'])
@login_required
def admin_delete_image(id):
    return delete_image_from_post(id)

def create_db():
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Функция для сохранения данных о посетителе в базу данных
def save_visitor(ip_address, user_agent):
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('''INSERT INTO visitors (ip_address, user_agent) VALUES (?, ?)''', (ip_address, user_agent))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # main1()
    create_db()
    print(' * Running on http://localhost:5000/ (Press Ctrl-C to quit)')
    print(' * Database is', app.config['SQLALCHEMY_DATABASE_URI'])
    app.run(debug=True)