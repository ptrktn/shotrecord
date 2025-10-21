import os
from flask import Flask, render_template, request, redirect, url_for
from models import db, Series, Shots

# Create the Flask application instance
app = Flask(__name__)

# Configure the database
# The database URI is loaded from an environment variable for security
# and defaults to a local SQLite file for development.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL_FIXME',
    'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the Flask-SQLAlchemy extension
db.init_app(app)
with app.app_context():
    # Create the database tables from the models defined in models.py
    db.create_all()

# def create_app():
#     app = Flask(__name__)
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#     db.init_app(app)

#     with app.app_context():
#         # from models import Series, Shots
#         db.create_all()

#     return app

@app.route("/", methods=["GET"])
def index():
    result = None
    return render_template("shot.html", result=result)
