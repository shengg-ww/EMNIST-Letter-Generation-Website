from application import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint

# User Model (Default Database)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)  # Store hashed passwords
    password = db.Column(db.String(120), nullable=False)  # Store hashed passwords
    role = db.Column(db.String(20), nullable=False)
    entries = db.relationship('Entry', backref='user', lazy=True)



class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    


