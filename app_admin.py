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

Misaka(app=app, escape=True, no_images=True,
       wrap=True, autolink=True, no_intra_emphasis=True,
       space_headers=True)



