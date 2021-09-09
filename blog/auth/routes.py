from glass import request, redirect, session, render_template

from rq import Retry

from blog.main import app, db, queue
from blog.models import User

import blog.tasks as task


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.user:
        return redirect('/')
    error = ''
    if request.method == 'POST':
        username = request.post.get('username')
        password = request.post.get('password')
        if not all((username, password)):
            error = 'provide username and password to login'
        else:
            user = db.query(User).filter_by(username=username).first()
            if not user:
                error = 'username not found'
            elif not user.check_password(password):
                error = 'invalid password'
            else:
                session['user_id'] = user.id
                queue.enqueue(task.on_login,user,retry=Retry(max=3))
                next_page = request.query.get('next', '/')
                return redirect(next_page)
    return render_template('auth/login.html', error=error)


@app.route('/user/logout')
def logout():
    if not request.user:
        return redirect('/')
    session.pop('user_id')
    return redirect('/')
