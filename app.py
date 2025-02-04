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
import databsaeforloc


app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
socketio = SocketIO(app, async_mode="threading")

with app.app_context():
    db.create_all()

Misaka(app=app, escape=True, no_images=True,
       wrap=True, autolink=True, no_intra_emphasis=True,
       space_headers=True)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('new_message')
async def handle_new_message(data):
    message = data['message']
    board = data['board']
    thread = data['thread']

      
    # Здесь должна быть логика сохранения нового сообщения в базу данных
    await save_message_to_db(message, board, thread)
    
    # Отправка обновленного списка сообщений всем подключенным клиентам
    updated_messages = await fetch_updated_messages(board, thread)
    socketio.emit('update_messages', {'messages': updated_messages}, broadcast=True)

# Функция для получения обновленных сообщений
async def fetch_updated_messages(board, thread):
    # Логика получения сообщений из базы данных
    messages = get_messages_from_db(board, thread)
    return messages

# Функция для сохранения сообщения в базу данных
async def save_message_to_db(message, board, thread):
    # Логика сохранения сообщения в базе данных
    pass

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



def location(ip: str):
    response = requests.get(f"http://ip-api.com/json/{ip}?lang=ru")
    if response.status_code == 404:
        print("Oops")
    result = response.json()
    if result["status"] == "fail":
        return main1("Enter the correct IP address")

    record = []

    for key, value in result.items():
        record.append(value)
        print(f"[{key.title()}]: {value}")
    return tuple(record)


def main1(start: str):
    print(start)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    try:
        new_data = location(ip)
        databsaeforloc.base(new_data)
    except ValueError:
        pass



if __name__ == '__main__':
    main1("Enter the IP address")
    print(' * Running on http://localhost:5000/ (Press Ctrl-C to quit)')
    print(' * Database is', app.config['SQLALCHEMY_DATABASE_URI'])
    app.run(debug=True)