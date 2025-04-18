from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

app = Flask(_name_)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///social_network.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    friends = db.relationship('Friendship', backref='user', lazy=True)

# Модель поста
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form['content']
    new_post = Post(content=content, user_id=session['user_id'])
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_image = Image(filename=filename, post=new_post)
            db.session.add(new_image)

    db.session.add(new_post)
    db.session.commit()
    
    flash('Пост успешно создан!', 'success')
    return redirect(url_for('index'))

# Модель комментария
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Модель дружбы
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Главная страница
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if len(username) < 3 or len(password) < 6:
            flash('Имя пользователя должно быть не менее 3 символов, а пароль - не менее 6 символов.', 'error')
            return redirect(url_for('register'))
        new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Имя пользователя уже занято. Пожалуйста, выберите другое.', 'error')
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'error')
    return render_template('login.html')

# Страница профиля пользователя
@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id).all()
    friends = Friendship.query.filter_by(user_id=user.id).all()
    friend_ids = [friend.friend_id for friend in friends]
    friend_users = User.query.filter(User.id.in_(friend_ids)).all()
    return render_template('profile.html', user=user, posts=posts, friends=friend_users)

# Создание поста
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form['content']
    new_post = Post(content=content, user_id=session['user_id'])
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_image = Image(filename=filename, post=new_post)
            db.session.add(new_image)

    db.session.add(new_post)
    db.session.commit()
    
    flash('Пост успешно создан!', 'success')
    return redirect(url_for('index'))

# Удаление поста
@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id == session.get('user_id'):
        db.session.delete(post)
        db.session.commit()
        flash('Пост успешно удален!', 'success')
    else:
        flash('Вы не можете удалить этот пост.', 'error')
    return redirect(url_for('index'))

# Добавление комментария
@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    if 'user_id' in session:
        content = request.form['content']
        if content:
            new_comment = Comment(content=content, post_id=post_id)
            db.session.add(new_comment)
            db.session.commit()
            flash('Комментарий успешно добавлен!', 'success')
        else:
            flash('Комментарий не может быть пустым.', 'error')
    return redirect(url_for('index'))

# Удаление комментария
@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    if comment.user_id == session.get('user_id'):
        db.session.delete(comment)
        db.session.commit()
        flash('Комментарий успешно удален!', 'success')
    else:
        flash('Вы не можете удалить этот комментарий.', 'error')
    return redirect(url_for('index'))

# Добавление друга
@app.route('/add_friend/<int:friend_id>')
def add_friend(friend_id):
    if 'user_id' in session:
        new_friendship = Friendship(user_id=session['user_id'], friend_id=friend_id)
        db.session.add(new_friendship)
        db.session.commit()
        flash('Друг добавлен!', 'success')
    return redirect(url_for('index'))

# Личная лента новостей
@app.route('/news_feed')
def news_feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    friends = Friendship.query.filter_by(user_id=user_id).all()
    friend_ids = [friend.friend_id for friend in friends]
    posts = Post.query.filter(Post.user_id.in_(friend_ids)).all()
    
    return render_template('news_feed.html', posts=posts)

# Выход
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('index'))

if _name_ == '_main_':
    db.create_all()  # Создание базы данных
    app.run(debug=True)

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref='images')

    class Message(db.Model):
    from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref='images')
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    