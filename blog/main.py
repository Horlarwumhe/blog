import html
import markdown
import logging
from logging.handlers import TimedRotatingFileHandler
import os

from glass import GlassApp
from glass import request, session, render_template
from glass.response import FileResponse, flash, messages


from redis import Redis
from rq import Queue

import blog.models as models
from blog.models import User, Post
import blog.tags as tags
from .utils import Paginator

app = GlassApp()
queue = Queue(connection=Redis())

logger = logging.getLogger("glass.app")
file = TimedRotatingFileHandler("logs/app.log", when='midnight')
file.setLevel(logging.DEBUG)
logger.addHandler(file)
file.setFormatter(
    logging.Formatter("%(asctime)s : %(message)s ",
                      datefmt="%d/%m/%Y %H:%M:%S %p"))

DB = os.environ.get('DB_ENGINE')
if not DB:
    logger.critical('database engine not found')
    exit(1)

app.config["DB_ENGINE"] = DB
app.config["TEMPLATES_FOLDER"] = os.path.join(os.getcwd(), "blog", "templates")
app.config["STATIC_FOLDER"] = os.path.join(os.getcwd(), "blog", "statics")
# app.config['TEMPLATE_BACKEND'] = 'jinja'
app.config["DEBUG"] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY','')
app.config['SESSION_COOKIE_MAXAGE'] = '3675443'


@app.error(404)
def handle_404(e):
    return render_template("errors/404.html"), 404


@app.before_request
def load_user():
    user_id = session.get("user_id")
    if not user_id:
        request.user = None
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


@app.template_env.filter("show_part")
def part(value):
    return value[:350]


@app.template_env.filter("markdown")
def mark(value):
    value = html.escape(value)
    return markdown.markdown(value)


@app.template_env.filter("url")
def url(value):
    value = "-".join(value.split())
    return value[:30]


app.template_env.globals['messages'] = messages


@app.template_env.filter('call')
def call(func):
    return func()