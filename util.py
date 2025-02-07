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
        file.thumbnail((200,200), Image.ANTIALIAS)
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
        flash('Must include a comment or image')
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
        OP = db.session.query(Posts).filter_by(id = op_id).first()
        if OP is None:
            flash('Post not found')
            return None
        OP.last_bump = datetime.now()
        db.session.commit()
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return None
def reply_count(op_id):
    replies = db.session.query(Posts).filter_by(op_id = op_id).all()
    if replies is None:
        return 0
    return len(replies)

def delete_post(id):
    post = db.session.query(Posts).filter_by(id=id).first()
    if post is None:
        flash('Post not found')
        return None
    post.deleted = True
    db.session.add(post)
    db.session.commit()

def delete_image(id):
    post = db.session.query(Posts).filter_by(id=id).one()
    post.deleted_image = True
    db.session.add(post)
    db.session.commit()
