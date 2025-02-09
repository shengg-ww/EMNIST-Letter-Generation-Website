from application import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, Boolean
from sqlalchemy.orm import validates

# User Model (Default Database)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)  
    password = db.Column(db.String(120), nullable=False)  # Store hashed passwords
    role = db.Column(db.String(20), nullable=False)
    entries = db.relationship('Entry', backref='user', lazy=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)



class Entry(db.Model):
    __tablename__ = 'entries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    letter= db.Column(db.String(1), index=True,nullable=False)
    image_data = db.Column(db.Text, nullable=False)  
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_favorite = Column(Boolean, default=False)  # New field for favorites
    colormap = db.Column(db.String(50))  # Add this line to store colormap


    __table_args__ = (
            CheckConstraint('LENGTH(letter) = 1', name='check_letter_length'),
        )
    @validates('letter')
    def validate_letter(self, key, value):
        if not isinstance(value, str):
            raise TypeError(f"Letter must be a string, got {type(value).__name__}")
        if len(value) != 1:
            raise ValueError("Letter must be a single character")
        return value
