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
from sqlalchemy.exc import SQLAlchemyError

def board_inexistent(name):
    """Проверяет, существует ли доска."""
    if name not in BOARDS:
        flash(f'Board {name} does not exist')
        return True
    return False

def upload_file():
    """Загружает файл и создает миниатюру."""
    file = request.files.get('file')
    if not file or not allowed_file(file.filename):
        return ''
    
    ext = file.filename.rsplit('.', 1)[1]
    fname = f"{int(time() * 1000)}.{ext}"
    file_path = join(UPLOAD_FOLDER, fname)
    file.save(file_path)

    # Создание миниатюры
    with Image.open(file_path) as img:
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        img.save(join(THUMBS_FOLDER, fname))
    
    return fname

def allowed_file(filename):
    """Проверяет, разрешено ли расширение файла."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def no_image():
    """Проверяет, отсутствует ли изображение."""
    if not request.files.get('file'):
        flash('Must include an image')
        return True
    return False

def no_content_or_image():
    """Проверяет, отсутствует ли контент или изображение."""
    if not request.files.get('file') and not request.form.get('post_content'):
        flash('Must include a comment or image')
        return True
    return False

def get_replies(thread):
    """Возвращает все ответы на тред."""
    return Posts.query.filter_by(op_id=thread, deleted=False).all()

def get_last_replies(thread):
    """Возвращает последние 5 ответов на тред."""
    return Posts.query.filter_by(op_id=thread, deleted=False).order_by(Posts.id.desc()).limit(5).all()

def get_OPs(board):
    """Возвращает последние 10 OP-постов на доске."""
    return Posts.query.filter_by(op_id='0', board=board, deleted=False).order_by(Posts.last_bump.desc()).limit(10).all()

def get_OPs_catalog(board):
    """Возвращает последние 100 OP-постов на доске для каталога."""
    return Posts.query.filter_by(op_id='0', board=board, deleted=False).order_by(Posts.last_bump.desc()).limit(100).all()

def get_OPs_all():
    """Возвращает последние 10 OP-постов со всех досок."""
    return Posts.query.filter_by(op_id='0', deleted=False).order_by(Posts.last_bump.desc()).limit(10).all()

def get_thread_OP(id):
    """Возвращает OP-пост треда по ID."""
    return Posts.query.filter_by(id=id).first()

def get_sidebar(board):
    """Возвращает информацию о доске для боковой панели."""
    return Boards.query.filter_by(name=board).first()

def new_post(board, op_id='0'):
    """Создает новый пост."""
    if not all(key in request.form for key in ['name', 'post_content']):
        flash('Must include name and post content')
        return None
    
    fname = upload_file()
    new_post = Posts(
        board=board,
        name=request.form['name'],
        text=request.form['post_content'],
        # date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        fname=fname,
        op_id=op_id,
        deleted=False
    )
    
    try:
        db.session.add(new_post)
        db.session.commit()
        return new_post
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error creating new post: {e}")
        flash('An error occurred while creating the post')
        return None

def bump_thread(op_id):
    """Обновляет время последнего бампа треда."""
    try:
        OP = Posts.query.filter_by(id=op_id).first()
        if not OP:
            flash('Post not found')
            return None
        
        OP.last_bump = datetime.now()
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error bumping thread: {e}")
        flash('An error occurred while bumping the thread')
        return None

def reply_count(op_id):
    """Возвращает количество ответов на тред."""
    return Posts.query.filter_by(op_id=op_id, deleted=False).count()

def delete_post(id):
    """Помечает пост как удаленный."""
    post = Posts.query.filter_by(id=id).first()
    if not post:
        flash('Post not found')
        return None
    
    post.deleted = True
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error deleting post: {e}")
        flash('An error occurred while deleting the post')

def delete_image(id):
    """Помечает изображение поста как удаленное."""
    post = Posts.query.filter_by(id=id).first()
    if not post:
        flash('Post not found')
        return None
    
    post.deleted_image = True
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error deleting image: {e}")
        flash('An error occurred while deleting the image')