import html
import markdown
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import urllib.parse

from glass import GlassApp
from glass import request, session, render_template
from glass.response import FileResponse, flash


from redis import Redis
from rq import Queue

import blog.models as models
from blog.models import User, Post
import blog.tags as tags
from .utils import Paginator
from .utils import secure_filename
from .config import Config

app = GlassApp()
app.config.from_object(Config)
queue = Queue(connection=Redis())

logger = logging.getLogger("glass.app")
file = TimedRotatingFileHandler("logs/app.log", when='midnight')
file.setLevel(logging.DEBUG)
logger.addHandler(file)
file.setFormatter(
    logging.Formatter("%(asctime)s : %(message)s ",
                      datefmt="%d/%m/%Y %H:%M:%S %p"))

DB = app.config['DB_ENGINE']
if not DB:
    logger.critical('database engine not found')
    exit(1)


@app.error(404)
def handle_404(e):
    return render_template("errors/404.html"), 404


@app.before_request
def load_user():
    user_id = session.get("user_id")
    if not user_id:
        request.user = None
    else:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            session.pop("user_id")
        request.user = user


@app.error(500)
def handle_500(e):
    db.rollback()
    return render_template("errors/500.html")


db = models.create_db(app)


@app.route("/")
def home():
    page_num = request.query.get("page", 1)
    try:
        page_num = int(page_num)
    except ValueError:
        page_num = 1
    posts = db.query(Post).filter(Post.id > 0).order_by(Post.date.desc())
    page = Paginator(posts, 4).get_page(page_num)
    return render_template("home.html", page=page, base='base.html')


@app.route('/media/<path:filename>')
def send_file(filename):
    path = os.path.join('blog/uploads', filename)
    if not os.path.exists(path):
        return render_template('errors/404.html')
    return FileResponse(path)


@app.route('/test')
def test():
    return render_template('test.html')


app.template_env.tags["date"] = tags.date
app.template_env.tags['current_time'] = tags.now


@app.template_env.filter("show_part")
def part(value):
    return '\n'.join(value.split('\n')[:5])
    # return value[:350]

@app.template_env.filter('e')
def escape(s):
    return html.escape(s,True)

@app.template_env.filter("markdown")
def mark(text):
    text = html.escape(text)
    text = markdown.markdown(text)
    return text

@app.template_env.filter('urlquote')
def quote(text):
    return urllib.parse.quote(text,'')

@app.template_env.filter("url")
def url(value):
    value = ' '.join(value.split()[:5])
    value = secure_filename(value).replace('_','-')
    return value


# app.template_env.globals


@app.template_env.filter('call')
def call(func):
    return func()
