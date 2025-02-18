from flask import Flask, request, redirect, render_template
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_misaka import Misaka
from util import *
from database import db
import config
# import asyncio
# import requests
# import ipaddress
import sqlite3



app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
# socketio = SocketIO(app, async_mode="threading")

with app.app_context():
    db.create_all()

Misaka(app=app, escape=True, no_images=True,
       wrap=True, autolink=True, no_intra_emphasis=True,
       space_headers=True)


@app.route('/')
def show_frontpage():


    return render_template('home.html'), "Hello World!"
    


@app.route('/visitors')
def show_visitors():
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('SELECT * FROM visitors')
    visitors = c.fetchall()
    conn.close()
    return render_template('index.html', visitors=visitors)

@app.route('/all/')
def show_all():
    OPs = get_OPs_all()
    entry_list = []
    for OP in OPs:
        replies = get_last_replies(OP.id)
        entry_list.append(OP)
        entry_list += replies[::-1]

    
    # Получение IP-адреса пользователя
    ip_address = request.remote_addr
    print(ip_address)
    
    # Получение User-Agent пользователя
    user_agent = request.headers.get('User-Agent')
    print(user_agent)
    # Сохранение данных в базу данных
    save_visitor(ip_address, user_agent)

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

@app.route('/del')
def delete():
    post_id = request.args.get('id')
    delete_post(post_id)
    board = request.args.get('board')
    thread = request.args.get('thread')
    return redirect('/' + board + '/' + thread)

@app.route('/admin/boards')
def admin_boards():
    boards = db.session.query(Boards).all()
    return render_template('admin_boards.html', boards=boards)

@app.route('/admin/boards/create', methods=['GET', 'POST'])
def admin_create_board():
    if request.method == 'POST':
        return create_board()
    return render_template('admin_create_board.html')

@app.route('/admin/boards/edit/<name>', methods=['GET', 'POST'])
def admin_edit_board(name):
    if request.method == 'POST':
        return edit_board(name)
    board = db.session.query(Boards).filter_by(name=name).first()
    return render_template('admin_edit_board.html', board=board)

@app.route('/admin/boards/delete/<name>', methods=['POST'])
def admin_delete_board(name):
    return delete_board(name)

@app.route('/admin/posts')
def admin_posts():
    posts = db.session.query(Posts).order_by(Posts.date.desc()).all()
    return render_template('admin_posts.html', posts=posts)

@app.route('/admin/posts/delete/<int:id>', methods=['POST'])
def admin_delete_post(id):
    return delete_post(id)

@app.route('/admin/posts/restore/<int:id>', methods=['POST'])
def admin_restore_post(id):
    return restore_post(id)

@app.route('/admin/posts/permanently_delete/<int:id>', methods=['POST'])
def admin_permanently_delete_post(id):
    return permanently_delete_post(id)

@app.route('/admin/posts/delete_image/<int:id>', methods=['POST'])
def admin_delete_image(id):
    return delete_image_from_post(id)



# def get_ip_location(ip: str) -> dict:
#     """
#     Получает информацию о геолокации IP-адреса.
    
#     :param ip: IP-адрес
#     :return: Словарь с данными о геолокации
#     """
#     try:
#         ipaddress.ip_address(ip)
#     except ValueError:
#         print(f"Неправильный IP-адрес: {ip}")
#         return None

#     # остальной код функции

#     try:
#         url = f"http://ip-api.com/json/{ip}?lang=ru"
#         response = requests.get(url)
#         response.raise_for_status()
#         data = response.json()
#         if data.get("status") == "fail":
#             raise ValueError(data.get("message"))
#         return data
#     except requests.exceptions.RequestException as e:
#         print(f"Ошибка запроса: {e}")
#         return None
#     except ValueError as e:
#         print(f"Неправильный IP-адрес: {e}")
#         return None

# def handle_ip_request(ip: str) -> None:
#     """
#     Обрабатывает запрос на получение информации о геолокации IP-адреса.
    
#     :param ip: IP-адрес
#     """
#     try:
#         location_data = get_ip_location(ip)
#         if location_data is None:
#             print("Не удалось получить информацию о геолокации")
#             return
#         print("Информация о геолокации:")
#         for key, value in location_data.items():
#             print(f"[{key.title()}]: {value}")
#     except Exception as e:
#         print(f"Ошибка: {e}")

# def main1() -> None:
#     """
#     Основная функция.
#     """
#     with app.test_request_context():
#         ip = request.remote_addr
#         if ip is None:
#             print("Не удалось получить IP-адрес")
#             return

#         handle_ip_request(ip)
        


#     with app.test_request_context():
#         ip = get_remote_addr()
#         if ip is None:
#             print("Не удалось получить IP-адрес")
#             return

#         handle_ip_request(ip)

#     with app.test_request_context():
#         ip = request.headers.get('X-Forwarded-For', request.remote_addr)
#         if ip is None:
#             print("Не удалось получить IP-адрес")
#             return

#         location_data = get_ip_location(ip)
#         if location_data is None:
#             print("Не удалось получить информацию о геолокации")
#             return

#         handle_ip_request(ip)
        

#     with app.test_request_context():
#         ip = request.headers.get('X-Forwarded-For', request.remote_addr)
#         if ip is None:
#             print("Не удалось получить IP-адрес")
#             return
#         handle_ip_request(ip)
        
#     with app.test_request_context():
#         ip = request.headers.get('X-Forwarded-For', request.remote_addr)
#         handle_ip_request(ip)

#         # Записываем вывод в файл output.txt
#         with open('output.txt', 'w') as f:
#             f.write(f"IP-адрес: {ip}\n")
#             location_data = get_ip_location(ip)
#             if location_data is not None:
#                 f.write("Информация о геолокации:\n")
#                 for key, value in location_data.items():
#                     f.write(f"[{key.title()}]: {value}\n")
#             else:
#                 f.write("Не удалось получить информацию о геолокации\n")





# Функция для создания базы данных и таблицы, если она еще не существует
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