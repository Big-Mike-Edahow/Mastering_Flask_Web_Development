# app.py
# Big Mike's Blog

import datetime
from datetime import date
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm as Form
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length
from sqlalchemy import func, desc

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Big Mike likes to keep things simple.'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['POSTS_PER_PAGE'] = 10

db = SQLAlchemy(app)
migrate = Migrate(app, db)

tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    posts = db.relationship('Post', backref='user', lazy='dynamic')

    def __init__(self, username=""):
        self.username = username

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Post(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255))
    text = db.Column(db.Text())
    publish_date = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    tags = db.relationship('Tag', secondary=tags, backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, title=""):
        self.title = title

    def __repr__(self):
        return "<Post '{}'>".format(self.title)


class Comment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    text = db.Column(db.Text())
    publish_date = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
    post_id = db.Column(db.Integer(), db.ForeignKey('post.id'))

    def __repr__(self):
        return "<Comment '{}'>".format(self.text[:15])


class Tag(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255))

    def __init__(self, title=""):
        self.title = title

    def __repr__(self):
        return "<Tag '{}'>".format(self.title)


class CommentForm(Form):
    name = StringField('Name', validators=[DataRequired(), Length(max=255)])
    text = TextAreaField(u'Comment', validators=[DataRequired()])


def sidebar_data():
    recent = Post.query.order_by(Post.publish_date.desc()).limit(5).all()
    top_tags = db.session.query(
        Tag, func.count(tags.c.post_id).label('total')
    ).join(tags).group_by(Tag).order_by(desc('total')).limit(5).all()

    return recent, top_tags

# Create Database with App Context
def create_db():
    with app.app_context():
        db.create_all()

username = "Big Mike"


@app.route('/')
@app.route('/<int:page>')
def index(page=1):
    posts = Post.query.order_by(Post.publish_date.desc()).paginate(page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    recent, top_tags = sidebar_data()

    return render_template('index.html', posts=posts, recent=recent, top_tags=top_tags)

@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        new_post = Post()
        new_post.title = request.form['title']
        new_post.text = request.form['text']
        new_post.publish_date =  datetime.datetime.now()
        new_post.user_id = 1
        
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/post/<int:post_id>', methods=('GET', 'POST'))
def post(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        new_comment = Comment()
        new_comment.name = form.name.data
        new_comment.text = form.text.data
        new_comment.post_id = post_id
        try:
            db.session.add(new_comment)
            db.session.commit()
        except Exception as e:
            flash('Error adding your comment: %s' % str(e), 'error')
            db.session.rollback()
        else:
            flash('Comment added', 'info')
        return redirect(url_for('post', post_id=post_id))

    post = Post.query.get_or_404(post_id)
    tags = post.tags
    comments = post.comments.order_by(Comment.publish_date.desc()).all()
    recent, top_tags = sidebar_data()
    username = "Big Mike"

    return render_template('post.html', post=post, tags=tags, comments=comments, recent=recent, top_tags=top_tags, form=form, username=username)


@app.route('/posts_by_tag/<string:tag_name>')
def posts_by_tag(tag_name):
    tag = Tag.query.filter_by(title=tag_name).first_or_404()
    posts = tag.posts.order_by(Post.publish_date.desc()).all()
    recent, top_tags = sidebar_data()

    return render_template('tag.html', tag=tag, posts=posts, recent=recent, top_tags=top_tags)


@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    create_db()
    app.run(debug=True)

