import os

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath('instance/posts.db')
DEBUG = False
SECRET_KEY = 'ya-hochu-piva'


BUMP_LIMIT         = 100
BOARDS             = ['teacher','learn','media','nsfw']
UPLOAD_FOLDER      = 'static/images/'
THUMBS_FOLDER      = 'static/thumbs/'
ALLOWED_EXTENSIONS =  set(['png','jpg','jpeg','gif'])