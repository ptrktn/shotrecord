from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


# Create the SQLAlchemy object
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    target_type = db.Column(db.String(64), nullable=False, default='10m ISSF Air Pistol')
    target_model = db.Column(db.String(64), nullable=False, default='Ecoaims TAR-170/60L')
    description = db.Column(db.String(64), nullable=False, default='Training Shooting')
    source_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_points = db.Column(db.Float, nullable=False)
    n = db.Column(db.Integer, nullable=False)
    total_t = db.Column(db.Float, nullable=True)
    user = db.relationship('User', backref=db.backref('series', lazy=True))

    def __repr__(self):
        return f"<Series {self.id}>"


class Shot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False, index=True)
    hit = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)
    shotnum = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Integer, nullable=True)
    y = db.Column(db.Integer, nullable=True)
    origx = db.Column(db.Integer, nullable=True)
    origy = db.Column(db.Integer, nullable=True)
    t = db.Column(db.Float, nullable=True)
    series = db.relationship('Series', backref=db.backref('shot', lazy=True))

    def __repr__(self):
        return f"<Shot {self.id} in Series {self.series_id} at ({self.x}, {self.y})>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    series = db.relationship('Series', backref=db.backref('metric', lazy=True))

    def __repr__(self):
        return f"<Metric {self.name}={self.value} for Series {self.series_id}>"
