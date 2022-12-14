from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask_sessionstore import Session
import jwt
from .models import User
from . import db, captcha, rmail

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    res = render_template('login.html')
    session['email'] = ''
    session['remember'] = ''
    return res

@auth.route('/login', methods=['POST'])
def login_post():
    session['email'] = email = request.form.get('email')
    password = request.form.get('password')
    session['remember'] = remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Неверное имя пользователя или пароль!')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)

    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    res = render_template('signup.html')
    session['email'] = ''
    session['name'] = ''
    return res

@auth.route('/signup', methods=['POST'])
def signup_post():
    session['email'] = email = request.form.get('email')
    session['name'] = name = request.form.get('name')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if not password or \
        not password2 or \
        not email or \
        not name or \
        not request.form.get('captcha'):
        flash('Все поля должны быть заполнены!')
        return redirect(url_for('auth.signup'))

    if not captcha.validate():
        flash('Неверный код с картинки!')
        return redirect(url_for('auth.signup'))

    if password != password2:
        flash('Пароли не совпадают!')
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Пользователь с такой почтой уже существует!')
        return redirect(url_for('auth.signup'))

    token = jwt.encode(
        {
            "email": email,
            "name": name,
            "password": password,
        }, current_app.config["SECRET_KEY"]
    )
    rmail.send(
        subject="проверка почты",
        receivers=email,
        html_template="email/verify.html",
        body_params={
            "name": name,
            "token": token
        }
    )
    return render_template("verify_email.html")

@auth.route("/verify-email/<token>")
def verify_email(token):
    data = jwt.decode(token, current_app.config["SECRET_KEY"])
    email = data["email"]
    name = data["name"]
    password = data["password"]
    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
