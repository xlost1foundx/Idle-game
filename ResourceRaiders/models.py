from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_end = db.Column(db.DateTime)
    resources = db.relationship('Resources', backref='user', uselist=False)
    buildings = db.relationship('Buildings', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Resources(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    wood = db.Column(db.Integer, default=0)
    stone = db.Column(db.Integer, default=0)
    food = db.Column(db.Integer, default=0)
    leather = db.Column(db.Integer, default=0)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    last_hunt = db.Column(db.DateTime, default=datetime.utcnow)

class Buildings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    woodcutter = db.Column(db.Integer, default=0)
    woodcutter_level = db.Column(db.Integer, default=1)
    quarry = db.Column(db.Integer, default=0)
    quarry_level = db.Column(db.Integer, default=1)
    farm = db.Column(db.Integer, default=0)
    farm_level = db.Column(db.Integer, default=1)