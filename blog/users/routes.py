from blog.main import app, db
from glass import render_template, request, redirect, session, flash
from blog.models import User
from blog.utils import url_b64decode
from blog import tasks


@app.route('/profile')
@app.route('/profile/<username>')
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
                user.password = user.hash_password(user.password)
                user.verified = False
                db.add(user)
                db.commit()

                try:
                    tasks.send_registration_token(user)
                except Exception as e:
                    print(e)
                    error = 'Failed send email. Internal Server Error'
                else:
                    flash("check your email to activate your account")
    if error:
        flash(error)
    return render_template('users/register.html', error=error)


@app.route('/u/reset_password',methods=['GET','POST'])
def reset_password():
    if request.method == 'POST':
        email = request.post.get('email', '')
        user = db.query(User).filter(User.email == email).first()
        if not user:
            flash("user with email the email address not found")
        else:
            # to make sure we can create token
            _ = user.create_reset_token()
            tasks.send_reset_token(user)
            flash("check your mail for password reset details")
    return render_template('users/reset_password.html', {})


@app.route('/reset/<user_id>/<token>')
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
    session['user_reset'] = user_id
    return redirect('/u/set_password')


@app.route('/u/set_password',methods=['GET','POST'])
def set_password():
    token = session.get('token')
    print('session token',token)
    if not token:
        return redirect('/')
    if request.method == 'POST':
        user_id = session.get('user_reset')
        if not user_id:
            return redirect('/')
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            if not user.check_reset_token(token):
                return redirect('/')
            password = request.post.get('password')
            user.password = user.hash_password(password)
            db.add(user)
            db.commit()
            session.pop('token')
            session.pop('user_reset')
            flash('password changed. login to continue')
            return redirect('/user/login')
    return render_template('users/set_password.html')


@app.route('/u/confirm/<token>')
def confirm_reg(token):
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
        print(valid, token)
        return "Token Invalid"
    print('verified')
    user.verified = True
    db.add(user)
    db.commit()
    session['user_id'] = user.id
    return redirect('/')
