from blog.main import app as blog_app

from blog.users import routes
from blog.posts import routes
from blog.auth import routes

app = blog_app

