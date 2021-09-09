import os


class ConfigBase:
    DB_ENGINE = os.environ.get("DB_ENGINE")
    DEBUG = False
    SECRET_KEY = os.environ.get("DB_ENGINE",'')
    SESSION_COOKIE_MAXAGE = 367544
    TEMPLATES_FOLDER = os.path.join(os.getcwd(), "blog", "templates")
    STATIC_FOLDER = os.path.join(os.getcwd(), "blog", "statics")
    DOMAIN_NAME = 'blog.horlarwumhe.me'


if os.environ.get("BLOG_TESTING"):

    class Config(ConfigBase):
        DB_ENGINE = "postgresql://blog:#blog@localhost:5432/blog_test"
        DEBUG = True
        DOMAIN_NAME = '127.0.0.1:8000'

else:

    class Config(ConfigBase):
        pass
