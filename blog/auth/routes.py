from glass import request, redirect, session, render_template
from glass import flash

from rq import Retry

from blog.main import app, db
from blog.models import User

import blog.tasks as task
from blog.utils import template


@app.route('/user/login', methods=['GET', 'POST'])
@template('auth/login.html')
def login():
    if request.user:
        return redirect('/')
    error = ''
    if request.method == 'POST':
        username = request.post.get('username')
        password = request.post.get('password')
        if not all((username, password)):
           return dict(error='provide username and password to login')
        user = db.query(User).filter_by(username=username).first()
        if not user:
            error = 'username not found'
        elif not user.check_password(password):
            error = 'invalid password'
        elif not user.verified:
            flash("Account has not been verified.")
            return redirect('/u/verify_account')
        else:
            session['user_id'] = user.id
            task.send_login_mail(user)
            next_page = request.query.get('next', '/')
            return redirect(next_page)
    return dict(error=error)


@app.route('/user/logout')
def logout():
    if not request.user:
        return redirect('/')
    session.pop('user_id')
    return redirect('/')
