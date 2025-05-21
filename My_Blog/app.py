# app.py
# My Blog

import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_bcrypt import Bcrypt
from forms import LoginForm, RegisterForm, CommentForm, PostForm

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Big Mike likes to keep things simple.'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['POSTS_PER_PAGE'] = 10

db = SQLAlchemy ()
db.init_app(app)

bc = Bcrypt()
bc.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    created = db.Column(
        db.DateTime(timezone=True), server_default=db.func.current_timestamp()
    )
    posts = db.relationship('Post', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password
    
class Post(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255))
    text = db.Column(db.Text())
    author = db.Column(db.String(50))
    publish_date = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

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


def sidebar_data():
    recent = Post.query.order_by(Post.publish_date.desc()).limit(5).all()
    return recent

# Create Database with App Context
def create_db():
    with app.app_context():
        db.create_all()


@app.route('/')
@app.route('/<int:page>')
def index(page=1):
    posts = Post.query.order_by(Post.publish_date.desc()).paginate(page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    recent = sidebar_data()

    return render_template('index.html', posts=posts, recent=recent)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data 
            user = User.query.filter_by(username=username).first()
            if user:
                if bc.check_password_hash(user.password, password):
                    login_user(user, remember=form.remember_me.data)
                    flash("You have been logged in.", category="success")
                    return redirect(url_for('index'))
                else:
                    flash("Incorrect password.")
                    return redirect(url_for('login'))
            else:
                flash("Username not found.")
                return redirect(url_for('login'))
        else:
            return render_template('login.html', form=form)
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'GET':
        return render_template('register.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            password = bc.generate_password_hash(password)
            user = User(username=username, password=password)

            db.session.add(user)
            db.session.commit()

            flash("Your account has been created. Please login.", category="success")
            return redirect(url_for('login'))

@app.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = PostForm()
    if request.method == 'GET':
        return render_template('create.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            new_post = Post()
            new_post.user_id = current_user.id
            new_post.title = form.title.data
            new_post.text = form.text.data
            new_post.author = current_user.username
            new_post.publish_date =  datetime.datetime.now()
            
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            return render_template("create.html", form=form)
    
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    # We want that the current user can edit is own posts
    if current_user.id == post.user.id:
        form = PostForm()
        if form.validate_on_submit():
            post.title = form.title.data
            post.text = form.text.data
            post.publish_date = datetime.datetime.now()
            db.session.merge(post)
            db.session.commit()
            return redirect(url_for('post', post_id=post.id))
        form.title.data = post.title
        form.text.data = post.text
        return render_template('edit.html', form=form, post=post)
    abort(403)

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
    comments = post.comments.order_by(Comment.publish_date.desc()).all()
    recent = sidebar_data()
    
    return render_template('post.html', post=post, comments=comments, recent=recent, form=form)
    
@app.route('/user/<string:username>')
def posts_by_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.publish_date.desc()).all()
    recent = sidebar_data()
    return render_template('user.html', username=username, posts=posts, recent=recent)

@app.route("/delete/<int:id>")
@login_required
def delete(id):
    post = Post.query.get(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", category="success")
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    create_db()
    app.run(debug=True, port=8080)
