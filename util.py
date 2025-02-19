from flask import request, flash, redirect, url_for, abort
from time import time
from os.path import join
from PIL import Image
from models import Boards, Posts
from __init__ import app
from database import db
from datetime import datetime
import logging
from config import *

def board_inexistent(name):
    
    if name not in BOARDS:
        flash('board ' + name + ' does not exist')
        return True

def upload_file():
    file = request.files['file']
    fname = ''
    if file and allowed_file(file.filename):
        # Save file as <timestamp>.<extension>
        ext = file.filename.rsplit('.', 1)[1]
        fname = str(int(time() * 1000)) + '.' + ext
        file.save(join(UPLOAD_FOLDER, fname))

        # Pass to PIL to make a thumbnail
        file = Image.open(file)
        file.thumbnail((200,200), Image.Resampling.LANCZOS)
        file.save(join(THUMBS_FOLDER, fname))
    return fname

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def no_image():
    if not request.files['file']:
        flash('Must include an image')
        return True
    return False

def no_content_or_image():
    if not request.files['file'] and request.form['post_content'] == '':
        flash('Ты долбаеб?')
        flash('Зачем отправлять пустое сообщение?')
        return True
    return False

def get_replies(thread):
    return db.session.query(Posts).filter_by(op_id = thread, deleted = 0).all()

def get_last_replies(thread):
    return db.session.query(Posts).filter_by(op_id = thread, deleted = 0).order_by(db.text('id desc')).limit(5)

def get_OPs(board):
    return db.session.query(Posts).filter_by(op_id = '0', board = board, deleted = 0).order_by(db.text('last_bump desc')).limit(10)

def get_OPs_catalog(board):
    return db.session.query(Posts).filter_by(op_id = '0', board = board, deleted = 0).order_by(db.text('last_bump desc')).limit(100)

def get_OPs_all():
    return db.session.query(Posts).filter_by(op_id = '0', deleted = 0).order_by(db.text('last_bump desc')).limit(10)

def get_thread_OP(id):
    return db.session.query(Posts).filter_by(id = id).all()

def get_sidebar(board):
    return db.session.query(Boards).filter_by(name=board).first()

def new_post(board, op_id = 1):
    if 'name' not in request.form or 'post_content' not in request.form:
        flash('Must include name and post content')
        return None
    newPost = Posts(board   = board,
                    name    = request.form['name'],
                    text    = request.form['post_content'],
                    date    = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    fname   = upload_file(),
                    op_id   = op_id, # Threads are normal posts with op_id set to 0
                    deleted = False)
    db.session.add(newPost)
    db.session.commit()
    return newPost

def bump_thread(op_id):
    try:
        print(id)
        print(op_id)
        print(id == op_id)
        OP = db.session.query(Posts).filter_by(op_id == id).first()
        if OP is None:
            flash('Post not found')
            flash('Заебало)')
            return None
        OP.last_bump = datetime.now()
        db.session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return None

def reply_count(op_id):
    replies = db.session.query(Posts).filter_by(op_id = op_id).all()
    if replies is None:
        return 0
    return len(replies)

# def delete_post(id):
#     post = db.session.query(Posts).filter_by(id=id).first()
#     if post is None:
#         flash('Post not found')
#         return None
#     post.deleted = True
#     db.session.add(post)
#     db.session.commit()

# def delete_image(id):
#     post = db.session.query(Posts).filter_by(id=id).one()
#     post.deleted_image = True
#     db.session.add(post)
#     db.session.commit()


def create_board():
    if 'name' not in request.form or 'long_name' not in request.form or 'description' not in request.form:
        flash('Must include name, long name, and description')
        return redirect(url_for('admin_boards'))

    name = request.form['name']
    long_name = request.form['long_name']
    description = request.form['description']
    hidden = 'hidden' in request.form  # Проверяем, отмечен ли чекбокс "hidden"

    new_board = Boards(name=name, long_name=long_name, description=description, hidden=hidden)
    db.session.add(new_board)
    db.session.commit()
    flash('Board created successfully')
    return redirect(url_for('admin_boards'))

def edit_board(name):
    board = db.session.query(Boards).filter_by(name=name).first()
    if not board:
        flash('Board not found')
        return redirect(url_for('admin_boards'))

    if 'long_name' in request.form:
        board.long_name = request.form['long_name']
    if 'description' in request.form:
        board.description = request.form['description']
    if 'hidden' in request.form:
        board.hidden = True
    else:
        board.hidden = False

    db.session.commit()
    flash('Board updated successfully')
    return redirect(url_for('admin_boards'))

def delete_board(name):
    board = db.session.query(Boards).filter_by(name=name).first()
    if not board:
        flash('Board not found')
        return redirect(url_for('admin_boards'))

    db.session.delete(board)
    db.session.commit()
    flash('Board deleted successfully')
    return redirect(url_for('admin_boards'))

def delete_post(id):
    post = db.session.query(Posts).filter_by(id=id).first()
    if not post:
        flash('Post not found')
        return redirect(url_for('admin_posts'))

    post.deleted = True
    db.session.commit()
    flash('Post deleted successfully')
    return redirect(url_for('admin_posts'))

def restore_post(id):
    post = db.session.query(Posts).filter_by(id=id).first()
    if not post:
        flash('Post not found')
        return redirect(url_for('admin_posts'))

    post.deleted = False
    db.session.commit()
    flash('Post restored successfully')
    return redirect(url_for('admin_posts'))

def permanently_delete_post(id):
    post = db.session.query(Posts).filter_by(id=id).first()
    if not post:
        flash('Post not found')
        return redirect(url_for('admin_posts'))

    db.session.delete(post)
    db.session.commit()
    flash('Post permanently deleted')
    return redirect(url_for('admin_posts'))

def delete_image_from_post(id):
    post = db.session.query(Posts).filter_by(id=id).first()
    if not post:
        flash('Post not found')
        return redirect(url_for('admin_posts'))

    post.fname = None  # Удаляем имя файла изображения
    db.session.commit()
    flash('Image deleted from post')
    return redirect(url_for('admin_posts'))