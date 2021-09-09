from glass import render_template, redirect, request
from glass.response import flash
from sqlalchemy.orm import query_expression
from blog.main import app, db
from blog.models import Comment, Post
from blog import utils

import os


@app.route('/post/<int:post_id>')
@app.route('/post/<int:post_id>/<str:title>')
def get_post(post_id, title=''):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        flash('post not found')
        return redirect('/')
    return render_template('posts/post.html', post=post)


@app.route('/post/create', methods=['POST', 'GET'])
@utils.login_require
def create_post():
    if not request.user:
        return redirect('/user/login?next=%s' % request.path)
    error = ''
    if request.method == 'POST':
        post = {**request.post}
        title = post.get('title')
        body = post.get('body')
        if not all((title, body)):
            error = ' enter title and body'
        else:
            image_url = post.get('imageurl', '')
            if not image_url:
                file = request.files.get('image')
                if file:
                    name = file.filename
                    ext = name.rsplit('.', 1)[-1]
                    if not os.path.exists('blog/uploads/posts'):
                        os.makedirs('blog/uploads/posts')
                    path = 'blog/uploads/posts/%s.%s' % (title.replace(
                        ' ', '_'), ext)
                    image_url = '/media/posts/%s.%s' % (title.replace(
                        ' ', '_'), ext)
                    file.save_as(path)
            post = Post(title=title,
                        body=body,
                        author_id=request.user.id,
                        image_url=image_url)
            db.add(post)
            db.commit()
            return redirect('/post/%s/%s' %
                            (post.id, post.title.replace(' ', '-')[:30]))
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
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return redirect('/')
    text = request.post.get('comment', '')
    comment = Comment(post_id=post.id, author_id=request.user.id, text=text)
    db.add(comment)
    db.commit()
    return redirect('/post/%s' % post.id)


@app.route('/<model>/<opt>/<int:id>',methods=['GET','POST'])
def edit_post(model, opt, id):
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
                return redirect('/post/%s'%result.id)
            else:
                result.text = request.post.get('text', result.text)
                redirect('/post/%s'%result.post.id)
        return render_template('posts/edit.html', post=result, model=m)
