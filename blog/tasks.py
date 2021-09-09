import time
from datetime import datetime
import logging
from email.mime.text import MIMEText
import smtplib
from smtplib import SMTP
import os
from threading import Thread

from glass.templating import render_template
from glass import request

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.broker import set_broker
import time
from dramatiq.results import Results

from blog.models import User
from blog.main import db,app

from .utils import url_b64encode

redis = RedisBroker()
redis.add_middleware(Results())
set_broker(redis)
logger = logging.getLogger('glass.app')


def on_login(user):
    time.sleep(10)
    print(" hello %s you login at ", user.username, str(datetime.now()))


def send_mail(from_, to, body, subject):
    message = MIMEText(body, 'html')
    message['To'] = to
    message['From'] = from_
    message['Subject'] = subject
    code, msg = 0, ''
    with SMTP('smtp.mailgun.org', 587) as smtp:
        try:
            username = os.environ.get("MAILGUN_USERNAME")
            password = os.environ.get("MAILGUN_PASSWORD")
            smtp.login(username, password)
            smtp.send_message(message)
        except smtplib.Exception as e:
            if hasattr(e, 'code'):
                code = e.code
            if hasattr(e, 'msg'):
                msg = e.msg
            logger.exception("Failed to send mail code=%s, msg=%s", code, msg)



def send_reset_token(user):
    # with app.app_ctx():
    #     user = db.query(User).filter(User.id == user_id).first()
    #     if not user:
    #     return
    def send():
        with app.mount():
            user_id = url_b64encode(str(user.id))
            from_ = "Password Reset <no-reply@%s>" % (os.environ.get("MAILGUN_DOMAIN"))
            to = user.email
            subject = 'Password Reset Request'
            body = render_template('email/reset_password.html', user=user,
                user_id=user_id,token=user.create_reset_token())
            print(body)
            send_mail(from_, to, body, subject)
    Thread(target=send).start()



def send_registration_token(user):
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     return
    print(user.id,user)
    from_ = "Account Confirmation <no-reply@%s>" % (
        os.environ.get("MAILGUN_DOMAIN"))
    to = user.email
    subject = 'Confirm Your Account'
    # with app.mount():
    body = render_template('email/registration_token.html', user=user)
    print(body)
    send_mail(from_, to, body, subject)

def send_login_mail(user):
    environ = request.environ
    def send():
        from_ = "Login Alert <no-reply@%s>" % (
            os.environ.get("MAILGUN_DOMAIN"))
        to = user.email
        subject = "Login Notification"
        with app.mount(environ):
            body = render_template('email/login_email.html',user=user)
            print(body)
            send_mail(from_, to, body, subject)
    Thread(target=send).start()
