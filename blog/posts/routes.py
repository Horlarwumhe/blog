from glass import render_template, redirect, request
from glass.response import flash
from sqlalchemy.orm import query_expression
from blog.main import app, db
from blog.models import Comment, Post
from blog import utils
from blog.utils import secure_filename
from urllib.parse import unquote

import os


# @app.route('/post/<int:post_id>')
@app.route('/post/<int:post_id>/<str:title>')
def get_post(post_id, title=''):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        flash('post not found')
        return redirect('/')
    return render_template('posts/post.html', post=post)


@app.route('/post/create', methods=['POST', 'GET'],view_name='create_post')
@utils.login_require
def create_post():
    if not request.user:
        return redirect('/user/login?next=%s' % request.path)
    error = ''
    if request.method == 'POST':
        post = {**request.post}
        title = post.get('title')
        body = post.get('body')
        publish = bool(post.get('publish'))
        if not all((title, body)):
            error = ' enter title and body'
        else:
            image_url = post.get('imageurl', '')
            if not image_url:
                file = request.files.get('image')
                if file:
                    print('file hrer file.name', file.filename)
                    name = file.filename
                    ext = name.rsplit('.', 1)[-1]
                    if not os.path.exists('blog/uploads/posts'):
                        os.makedirs('blog/uploads/posts')
                    path_name = secure_filename(title)
                    path = 'blog/uploads/posts/%s.%s' % (path_name, ext)
                    image_url = '/media/posts/%s.%s' % (path_name, ext)
                    file.save_as(path)
                else:
                    print('no file upload..')
            post = Post(title=title,
                        body=body,
                        author_id=request.user.id,
                        image_url=image_url,
                        publish=publish)
            db.add(post)
            db.commit()
            title = secure_filename(post.title)
            return redirect('/post/%s/%s' % (post.id, title))
    return render_template('posts/create.html', error=error)


@app.route('/delete/<int:post_id>/<title>')
@app.route('/delete/<int:post_id>')
@utils.login_require
def delete_post(post_id, title=''):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        if not request.user.id == post.author.id:
            return redirect('/')
        db.delete(post)
        db.commit()
    return redirect('/')


@app.route('/post/comment/<int:post_id>/', methods=['GET', 'POST'])
@utils.login_require
def add_comment(post_id):
    if not request.method == 'POST':
        return "...."
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return redirect('/')
    text = request.post.get('comment', '')
    comment = Comment(post_id=post.id, author_id=request.user.id, text=text)
    db.add(comment)
    db.commit()
    return redirect('/post/%s/%s' % (post.id, secure_filename(post.title)))


# /post/edit/id
# / post/delete/id
@app.route('/<model>/<opt>/<int:id>/<title>', methods=['GET', 'POST'])
@app.route('/<model>/<opt>/<int:id>', methods=['GET', 'POST'])
def edit_post(model, opt, id, title=None):
    if not request.user:
        return redirect('/user/login')
    if model == 'post':
        model = Post
    elif model == 'comment':
        model = Comment
    else:
        return render_template('errors/404.html'), 404
    if opt not in ('edit,delete'):
        return render_template('errors/404.html'), 404
    result = db.query(model).filter(model.id == id).first()
    if not result:
        return redirect(request.query.get('next', '/'))
    if not request.user.id == result.author.id:
        return redirect(request.query.get('next', '/'))
    if opt == 'delete':
        db.delete(result)
        db.commit()
        return redirect(request.query.get('next', '/'))
    else:
        m = model.__name__.lower()
        if request.method == 'POST':
            if m == 'post':
                result.body = request.post.get('body', result.body)
                result.title = request.post.get('title', result.title)
                title = secure_filename(result.title)
                result.publish = bool(request.post.get('publish'))
                print(request.post.get('imageurl'), '======')
                result.image_url = (request.post.get('imageurl')
                                    or result.image_url)
                print(result.image_url, '--------')
                db.add(result)
                db.commit()
                return redirect('/post/%s/%s' % (result.id, title))
            else:
                result.text = request.post.get('text', result.text)
                db.add(result)
                db.commit()
                print('commited')
                title = result.post.title.replace(' ', '-')
                return redirect('/post/%s/%s' % (result.post.id, title))
        return render_template('posts/edit.html', post=result, model=m)
