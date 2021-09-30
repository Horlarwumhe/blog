from blog.main import app, db
from glass import render_template, request, redirect, session, flash
from blog.models import User
from blog.utils import url_b64decode, login_require
from blog import tasks


@app.route('/profile',view_name='profileold')
@app.route('/profile/<username>',view_name='profile')
@app.route('/u/profile/<username>',view_name='userprofile')
def userprofile(username=None):
    if not request.user and not username:
        return redirect('/user/login')
    if not username:
        user = request.user
    else:
        user = db.query(User).filter(User.username == username).first()
    if not user:
        return 'user not found %s' % username, 404
    return render_template('users/profile.html', user=user)


@app.route('/user/register', methods=['GET', 'POST'])
def register():
    error = ''
    mailsent = False
    if request.user:
        return redirect('/')
    if request.method == "POST":
        username = request.post.get('username')
        password = request.post.get('password')
        email = request.post.get('email')
        if not all((username, password, email)):
            error = 'all fields are required'
        else:
            user = db.query(User).filter_by(username=username).first()
            db_mail = db.query(User).filter_by(email=email).first()
            if user:
                error = 'username already exists'
            elif db_mail:
                error = 'email already exists'
            else:
                user = User(username=username, password=password, email=email)
                user.set_password(user.password)
                user.verified = False
                db.add(user)
                db.commit()
                tasks.send_registration_token(user)
                mailsent = True
                flash("check your email to activate your account")
    if error:
        flash(error)
    return render_template('users/register.html', error=error,
           mailsent=mailsent)


@app.route('/u/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.post.get('email', '')
        user = db.query(User).filter(User.email == email).first()
        if not user:
            flash("user the email address not found")
        else:
            # to make sure we can create token
            # _ = user.create_reset_token()
            tasks.send_reset_token(user)
            flash("check your mail for password reset details")
    return render_template('users/reset_password.html', {})


@app.route('/reset/<user_id>/<token>',view_name='reset')
@app.route('/reset_password/<user_id>/<token>',view_name='do_reset')
def do_reset(user_id, token):
    try:
        user_id = int(url_b64decode(user_id))
    except ValueError as e:
        return "invalid token or user id"
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return redirect('/')
    if not user.check_reset_token(token):
        return 'token expired or invalid'
    session['token'] = token
    session['user_reset_id'] = user_id
    return redirect('/u/set_password')


@app.route('/u/change_password', methods=['GET', 'POST'])
@login_require
def change_password():
    error = ''
    if request.method == 'POST':
        old_password = request.post.get('oldpassword')
        if request.user.hash_password(old_password) != request.user.password:
            error = "Incorrect password"
        else:
            password = request.post.get('password')
            user = db.query(User).filter(User.id == request.user.id).first()
            user.set_password(password)
            db.add(user)
            db.commit()
            flash("Password changed")
            app.redis.delete('user-%s'%request.user.id)
            return redirect('/')
    return render_template('users/change_password.html',error=error)


@app.route('/u/set_password', methods=['GET', 'POST'])
def set_password():
    token = session.get('token')
    if not token:
        return redirect('/')
    if request.method == 'POST':
        user_id = session.pop('user_reset_id')
        session.pop('token')
        if not user_id:
            return redirect('/')
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            if not user.check_reset_token(token):
                return redirect('/')
            password = request.post.get('password')
            user.set_password(password)
            db.add(user)
            db.commit()
            app.redis.delete('user-%s'%user.id)
            flash('Password changed. login to continue')
            return redirect('/user/login')
    return render_template('users/set_password.html')


@app.route('/u/verify_account', methods=['GET', 'POST'])
def verify_account():
    error = ''
    if request.method == 'POST':
        email = request.post.get('email')
        user = db.query(User).filter(User.email == email).first()
        if not user:
            error = "user not found"
        else:
            tasks.send_registration_token(user)
            flash("check your email to activate your account")
    return render_template('users/verify_account.html', error=error)

@app.route('/u/verify_account/<token>')
def verify_account_token(token):
    try:
        user_id, _ = token.split('.', 1)
        user_id = int(url_b64decode(user_id))
    except (ValueError, TypeError):
        return 'Token invalid'
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return "Not Found"
    valid = user.create_reg_token()
    if valid != token:
        return "Token Invalid"
    user.verified = True
    db.add(user)
    db.commit()
    session['user_id'] = user.id
    return redirect('/')

@app.route('/u/<username>')
def userprofile(username=None):
    if not request.user and not username:
        return redirect('/user/login?next=%s'%request.path)
    if not username:
        user = request.user
    else:
        user = db.query(User).filter(User.username == username).first()
    if not user:
        return 'user not found %s' % username, 404
    return render_template('users/profile.html', user=user)
