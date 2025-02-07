# This configuration file is provided to make testing easy. Your real
# configuration should not be checked into source control. See:
# http://blog.arvidandersson.se/2013/06/10/credentials-in-git-repos
import os

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath('instance/posts.db')
DEBUG = False
SECRET_KEY = 'ya-hochu-piva'


BUMP_LIMIT         = 100
BOARDS             = ['create','learn','media','meta, NSFW']
UPLOAD_FOLDER      = 'static/images/'
THUMBS_FOLDER      = 'static/thumbs/'
ALLOWED_EXTENSIONS =  set(['png','jpg','jpeg','gif'])
