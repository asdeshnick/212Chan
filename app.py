from flask import Flask, request, redirect, render_template
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_misaka import Misaka
from util import *
from database import db
import config
import asyncio
import requests
# import using_IP.databsaeforloc as databsaeforloc
import ipaddress



app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
# socketio = SocketIO(app, async_mode="threading")

with app.app_context():
    db.create_all()

Misaka(app=app, escape=True, no_images=True,
       wrap=True, autolink=True, no_intra_emphasis=True,
       space_headers=True)

# @socketio.on('connect')
# def handle_connect():
#     print("Client connected")

# @socketio.on('new_message')
# async def handle_new_message(data):
#     message = data['message']
#     board = data['board']
#     thread = data['thread']

      
#     # Здесь должна быть логика сохранения нового сообщения в базу данных
#     await save_message_to_db(message, board, thread)
    
#     # Отправка обновленного списка сообщений всем подключенным клиентам
#     updated_messages = await fetch_updated_messages(board, thread)
#     socketio.emit('update_messages', {'messages': updated_messages}, broadcast=True)

# # Функция для получения обновленных сообщений
# async def fetch_updated_messages(board, thread):
#     # Логика получения сообщений из базы данных
#     messages = get_messages_from_db(board, thread)
#     return messages

# # Функция для сохранения сообщения в базу данных
# async def save_message_to_db(message, board, thread):
#     # Логика сохранения сообщения в базе данных
#     pass

@app.route('/')
def show_frontpage():
    return render_template('home.html')


# @app.route('/all/')
# def show_frontpage():
#     return render_template('home.html')

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

@app.route('/del')
def delete():
    post_id = request.args.get('id')
    delete_post(post_id)
    board = request.args.get('board')
    thread = request.args.get('thread')
    return redirect('/' + board + '/' + thread)




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


if __name__ == '__main__':
    # main1()
    print(' * Running on http://localhost:5000/ (Press Ctrl-C to quit)')
    print(' * Database is', app.config['SQLALCHEMY_DATABASE_URI'])
    app.run(debug=True)