from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqlamodel import ModelView
from database import db
import app

admin = Admin(app)
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Post, db.session))

class MyUserAdmin(ModelView):
  def __init__(self, session, name, excluded=None):
    if excluded:
      self.excluded_list_columns = excluded
   
    super(MyUserAdmin, self).__init__(User, session, name=name)

admin = Admin(app)
admin.add_view(MyUserAdmin(db.session, 'View1', ('password',)))
admin.add_view(MyUserAdmin(db.session, 'View2', ('email','password')))