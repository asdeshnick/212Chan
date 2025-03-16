import os

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath('instance/posts.db')
DEBUG = False
SECRET_KEY = '43534h5hg5jhkj5hh456345h376454334566k56ekjykvh5465653v4h45b35244374564n6mn464'
SQLALCHEMY_TRACK_MODIFICATIONS = False

BUMP_LIMIT         = 100
BOARDS             = ['teacher','learn','media','nsfw']
UPLOAD_FOLDER      = 'static/images/'
THUMBS_FOLDER      = 'static/thumbs/'
ALLOWED_EXTENSIONS =  set(['png','jpg','jpeg','gif'])