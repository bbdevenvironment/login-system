from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pro_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    date = db.Column(db.String(50))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    content = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access Denied: Admins Only!", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function




@app.route('/')
def home():
    events = Event.query.all()
    return render_template('index.html', events=events)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form.get('password'))
        new_user = User(username=request.form.get('username'), password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('admin_panel') if user.is_admin else url_for('home'))
        flash('Invalid Credentials')
    return render_template('login.html')

@app.route('/contact', methods=['POST'])
def send_message():
    new_msg = Message(name=request.form.get('name'), email=request.form.get('email'), content=request.form.get('content'))
    db.session.add(new_msg)
    db.session.commit()
    flash('Message sent!')
    return redirect(url_for('home'))


@app.route('/admin')
@admin_required
def admin_panel():
    events = Event.query.all()
    messages = Message.query.all()
    users = User.query.all()
    return render_template('admin.html', events=events, messages=messages, users=users)

@app.route('/admin/promote/<int:id>')
@admin_required
def promote_user(id):
    user = User.query.get(id)
    if user:
        user.is_admin = True
        db.session.commit()
        flash(f'{user.username} promoted to Admin!')
    return redirect(url_for('admin_panel'))



@app.route('/admin/add_event', methods=['POST'])
@admin_required
def add_event():
    db.session.add(Event(title=request.form.get('title'), date=request.form.get('date'), 
                         location=request.form.get('location'), description=request.form.get('description')))
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password=generate_password_hash('admin123'), is_admin=True))
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)