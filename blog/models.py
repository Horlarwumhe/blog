import hashlib
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
secret = '<some app secret>'
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    def __repr__(self):
        return '<User id=%s, username=%s' % (self.id, self.username)

    @classmethod
    def hash_password(cls, password):
        return hashlib.sha1(password.encode() + secret.encode()).hexdigest()

    def check_password(self, password):
        password = self.hash_password(password)
        return self.password == password


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship('User', backref='posts')
    date = Column(DateTime,default=datetime.utcnow)
    body = Column(String,nullable=False)
    image_url = Column(String)

    def __repr__(self):
        if self.author:
            author = self.author.username
        else:
            author = 'admin'
        return 'Post id=%s, author=%s' % (self.id, author)


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    post = relationship('Post', backref='comments')
    author_id = Column(Integer, ForeignKey('users.id'))
    text = Column(String, nullable=False)
    author = relationship('User', backref='comments')
    date = Column(DateTime,default=datetime.utcnow)

    def __repr__(self):
        if self.post:
            post = self.post.id
        else:
            post = 'None'
        return '<Comment post=%s' % post


def create_db(app):
    engine = create_engine(app.config['DB_ENGINE'] or 'sqlite:memory')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
