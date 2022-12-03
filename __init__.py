import uuid
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_sessionstore import Session
from flask_session_captcha import FlaskSessionCaptcha
from flask_redmail import RedMail

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
captcha = None
rmail = None

def create_app(db_host, db_port, db_usr, db_pwd, em_host, em_port, em_usr, em_pwd):
    global captcha
    global rmail

    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid4())

    db_uri = 'mysql+pymysql://{}:{}@{}:{}/{}'. \
        format(
            db_usr,
            db_pwd,
            db_host,
            db_port,
            'zbportal'
        )

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

    db.init_app(app)

    app.config['CAPTCHA_ENABLE'] = True
    app.config['CAPTCHA_LENGTH'] = 5
    app.config['CAPTCHA_WIDTH'] = 160
    app.config['CAPTCHA_HEIGHT'] = 60
    # In case you want to use another key in your session to store the captcha:
    app.config['CAPTCHA_SESSION_KEY'] = 'captcha_image'
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    # Configure the sender
    app.config["EMAIL_HOST"] = em_host
    app.config["EMAIL_PORT"] = em_port
    app.config["EMAIL_USERNAME"] = em_usr
    app.config["EMAIL_PASSWORD"] = em_pwd
    # Enables server session
    Session(app)
    # Initialize FlaskSessionCaptcha
    with app.app_context():
        captcha = FlaskSessionCaptcha(app)
    rmail = RedMail(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
