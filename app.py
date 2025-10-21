import os
import uuid
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from models import db, Series, Shots

def create_app():
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
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB

    # Initialize the Flask-SQLAlchemy extension
    db.init_app(app)

    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()

    return app

app = create_app()

@app.route("/", methods=["GET"])
def index():
    result = None
    return render_template("shot.html", result=result)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in the request', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    filename = str(uuid.uuid4()) # secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return 'File uploaded successfully', 200
