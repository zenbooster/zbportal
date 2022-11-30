from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.BigInteger, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(320), unique=True)
    password = db.Column(db.String(128))
    name = db.Column(db.String(32), unique=True)
