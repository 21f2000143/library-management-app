from flask_login import UserMixin
from . import db
from datetime import datetime

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(128), nullable=False)
    is_librarian = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), default = datetime.now())
    purchases = db.relationship('Purchase', backref='buyer', lazy=True)
    user_books = db.relationship('Register', backref='user', lazy=True)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    books = db.relationship('Book', backref='section', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.BLOB, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

class Register(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    book_name = db.Column(db.String(100), nullable=False)
    request_status = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    date_issued = db.Column(db.DateTime)
    requested_date = db.Column(db.DateTime, default = datetime.now())
    return_date = db.Column(db.DateTime)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)