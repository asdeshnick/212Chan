from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, request, redirect, render_template, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from logging.handlers import RotatingFileHandler
from wtforms.validators import DataRequired
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_misaka import Misaka
from flask_wtf import FlaskForm
from datetime import datetime
from database import db
from util import *
import sqlite3
import logging
import config
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor


app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")
executor = ThreadPoolExecutor(max_workers=4)

with app.app_context():
    db.create_all()

Misaka(app=app, escape=True, no_images=True,
       wrap=True, autolink=True, no_intra_emphasis=True,
       space_headers=True)


# Модель пользователя
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'  
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
login_manager.login_message_category = "error"


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
            login_user(user) 
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('admin_boards'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Выход пользователя
    logout_user()
    # Перенаправление на страницу входа
    response = redirect(url_for('show_all'))
    # Удаление сессионной куки
    response.delete_cookie('session')
    # Запрет кеширования
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    # Уведомление об успешном выходе
    flash('Вы успешно вышли!', 'success')
    return response

@app.after_request
def add_no_cache_headers(response):
    # Запрет кеширования для всех страниц
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.context_processor
def inject_version():
    # Автоматическая версия для статики
    return dict(version=datetime.now().timestamp())

@login_required
@app.route('/admin/dashboard')
def admin_dashboard():
    return "Welcome to the Admin Dashboard!"

@app.route('/admin/boards')
@login_required
def admin_boards():
    boards = db.session.query(Boards).all()
    return render_template('admin_boards.html', boards=boards)



# Настройка логирования
def setup_logging():
    # Создаем папку для логов если ее нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Формат логов
    log_format = '%(asctime)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
    formatter = logging.Formatter(log_format)
    
    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        'logs/application.log',
        maxBytes=1024 * 1024 * 5,  # 5MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Настройка логгера приложения
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Логирование SQLAlchemy
    sql_logger = logging.getLogger('sqlalchemy.engine')
    sql_logger.setLevel(logging.WARNING)
    
    app.logger.info('Application startup at %s', datetime.now())

# Вызываем настройку логирования после создания app
setup_logging()

# Утилита для логирования действий
def log_action(action, details=None, level='info'):
    user = current_user.username if current_user.is_authenticated else 'Anonymous'
    ip = request.remote_addr
    message = f"User: {user}, IP: {ip}, Action: {action}"
    if details:
        message += f", Details: {details}"
    
    if level == 'info':
        app.logger.info(message)
    elif level == 'warning':
        app.logger.warning(message)
    elif level == 'error':
        app.logger.error(message)
    elif level == 'critical':
        app.logger.critical(message)

# Пример добавления логирования в маршруты
@app.route('/admin/boards/create', methods=['GET', 'POST'])
@login_required
def admin_create_board():
    if not current_user.is_admin:
        log_action("Unauthorized access attempt", "Tried to create board", 'warning')
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            log_action("Board creation failed", "Missing name", 'warning')
            flash('Board name is required', 'error')
            return redirect(url_for('admin_create_board'))
        
        existing_board = Boards.query.filter_by(name=name).first()
        if existing_board:
            log_action("Board creation failed", f"Board {name} already exists", 'warning')
            flash('Board with this name already exists', 'error')
            return redirect(url_for('admin_create_board'))
        
        new_board = Boards(name=name, description=description)
        db.session.add(new_board)
        db.session.commit()
        
        log_action("Board created", f"Name: {name}")
        flash('Board created successfully!', 'success')
        return redirect(url_for('admin_boards'))
    
    return render_template('admin/boards/create.html')

# Добавляем логирование в обработчики ошибок
@app.errorhandler(404)
def page_not_found(e):
    log_action("404 Not Found", f"Path: {request.path}", 'warning')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    log_action("500 Internal Server Error", f"Path: {request.path}\nError: {str(e)}", 'error')
    return render_template('errors/500.html'), 500


@login_required
@app.route('/admin/boards/edit/<name>', methods=['GET', 'POST'])
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
    if ip_address == None:
        print("None")
    else:
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
    return render_template('index-visitors.html', visitors=visitors)

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

@socketio.on('new_post')
def handle_new_post(data):
    board = data['board']
    thread = data.get('thread')
    emit('post_added', {'board': board, 'thread': thread}, broadcast=True)

@socketio.on('new_reply')
def handle_new_reply(data):
    board = data['board']
    thread = data['thread']
    emit('reply_added', {'board': board, 'thread': thread}, broadcast=True)

@app.route('/add', methods=['POST'])
def new_thread():
    board = request.form['board']
    if no_image():
        return redirect('/' + board + '/')

    def process_new_thread():
        newPost = new_post(board)
        newPost.last_bump = datetime.now()
        db.session.add(newPost)
        db.session.commit()
        socketio.emit('new_post', {'board': board})

    executor.submit(process_new_thread)
    return redirect('/' + board + '/')

@app.route('/add_reply', methods=['POST'])
def add_reply():
    board = request.form['board']
    thread = request.form['op_id']
    subject = request.form['subject']
    
    if no_content_or_image():
        return redirect('/' + board + '/')

    def process_new_reply():
        newPost = new_post(board, thread)
        db.session.add(newPost)
        if reply_count(thread) < BUMP_LIMIT:
            bump_thread(thread)
        db.session.commit()
        socketio.emit('new_reply', {'board': board, 'thread': thread})

    executor.submit(process_new_reply)
    return redirect('/' + board + '/')

# Функция для сохранения данных о посетителе в базу данных
def save_visitor(ip_address, user_agent):
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('''INSERT INTO visitors (ip_address, user_agent) VALUES (?, ?)''', (ip_address, user_agent))
    conn.commit()
    conn.close()

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


if __name__ == '__main__':
    create_db()
    print(' * Running on http://localhost:5000/ (Press Ctrl-C to quit)')
    print(' * Database is', app.config['SQLALCHEMY_DATABASE_URI'])
    socketio.run(app, debug=True)