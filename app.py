# import eventlet
# eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, copy_current_request_context
from flask_socketio import SocketIO, send, emit
from models import db, Series, Shots
from data_importer import import_data_from_file
import os
import uuid
import threading

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
    app.config['SECRET_KEY'] = str(uuid.uuid4())

    # Initialize the Flask-SQLAlchemy extension
    db.init_app(app)

    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()

    return app

app = create_app()
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/shot", methods=["GET"])
def shot():
    result = None
    return render_template("shot.html", result=result)

@app.route('/upload', methods=['POST'])
def upload_file():
    @copy_current_request_context
    def import_data_from_file_wrapper(filename):
        import_data_from_file(filename)

    if 'file' not in request.files:
        return 'No file part in the request', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400

    filename = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
    file.save(filename)
    thread = threading.Thread(target=import_data_from_file_wrapper, args=(filename,))
    thread.start()

    return 'File uploaded successfully', 200


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('welcome', {'message': 'Hello from the server!'})


@socketio.on('message')
def handle_message(msg):
    print('Received message: ' + msg)
    socketio.send('Echo: ' + msg)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
