import time
from datetime import datetime


def on_login(user):
    time.sleep(10)
    print(" hello %s you login at ", user.username, str(datetime.now()))
