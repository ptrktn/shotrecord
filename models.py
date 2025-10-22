from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

# Create the SQLAlchemy object
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # FIXME: separate id and imported IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_points = db.Column(db.Float, nullable=False)
    total_t = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Series {self.id}>"

class Shots(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)
    hit = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)
    shotnum = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Integer, nullable=True)
    y = db.Column(db.Integer, nullable=True)
    t = db.Column(db.Float, nullable=True)
    series = db.relationship('Series', backref=db.backref('shots', lazy=True))

    def __repr__(self):
        return f"<Shot {self.id} in Series {self.series_id} at ({self.x}, {self.y})>"
