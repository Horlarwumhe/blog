import os


class ConfigBase:
    DB_ENGINE = os.environ.get("DB_ENGINE")
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY",'3da64212a3e286ccd756f807df4393')
    SESSION_COOKIE_MAXAGE = 367544
    TEMPLATES_FOLDER = os.path.join(os.getcwd(), "blog", "templates")
    STATIC_FOLDER = os.path.join(os.getcwd(), "blog", "statics")
    # SERVER_NAME = DOMAIN_NAME = 'http://blog.horlarwumhe.me'
    MAX_CONTENT_LENGTH = 5_000_000 # < 5MB
    MAIL_DOMAIN = 'http://blog.horlarwumhe.me'


if os.environ.get("BLOG_ENV") == 'dev':

    class Config(ConfigBase):
        DB_ENGINE = "postgresql://blog:#blog@localhost:5432/blog_test"
        DEBUG = True
        SERVER_NAME = DOMAIN_NAME = ''

else:

    class Config(ConfigBase):
        pass
