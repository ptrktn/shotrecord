# Workaround for compatibility issues with eventlet and Flask-SocketIO
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, copy_current_request_context, jsonify
from flask import abort, session, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, send, emit
from models import db, Series, User
from data_importer import import_data_from_file
from sqlalchemy.orm import joinedload
from sqlalchemy import func, extract
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from plots import weekly_series_plot, generate_target


def create_app():
    # Create the Flask application instance
    app = Flask(__name__)

    # Configure the database
    # The database URI is loaded from an environment variable for security
    # and defaults to a local SQLite file for development.
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URI',
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', str(uuid.uuid4()))

    # Initialize the Flask-SQLAlchemy extension
    db.init_app(app)

    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()

    return app


app = create_app()
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route("/points/<name>", methods=['GET'])
def get_series_points(name):
    results = (
        db.session.query(Series.created_at, Series.total_points)
        .filter(Series.name == name)
        .order_by(Series.created_at.asc())
        .all()
    )

    if not results:
        abort(404, description=f"No series found for user '{name}'")

    data = [
        (r.created_at.isoformat(timespec='seconds'), round(r.total_points, 1))
        for r in results
    ]
    return render_template("points.html", name=name, data=data)


@app.route('/trend', methods=['GET'])
@login_required
def get_series_trend():
    results = (
        db.session.query(Series.total_points)
        .filter(Series.user_id == current_user.id)
        .order_by(Series.created_at.asc())
        .all()
    )

    if not results:
        abort(404, description=f"No series found for user '{current_user.username}'")

    data = [round(r.total_points, 1) for r in results]

    return render_template("trend.html", data=data)


@app.route('/series/<int:series_id>', methods=['GET'])
@login_required
def get_series(series_id):
    series = (
        db.session.query(Series)
        .options(joinedload(Series.shot), joinedload(Series.metric))
        .filter(Series.id == series_id, Series.user_id == current_user.id)
        .first()
    )

    if not series:
        abort(404, description='Series not found')

    return render_template('series.html', series=series)


@app.route("/shot", methods=['GET'])
def shot():
    result = None
    return render_template("shot.html", result=result)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    @copy_current_request_context
    def import_data_from_file_wrapper(filename, user_id):
        import_data_from_file(filename, user_id)
        # FIXME: socketio.emit('notifications', {'message': f"User {name} file import completed!"})

    if request.method == "POST":
        if 'file' not in request.files:
            return 'No file part in the request', 400

        file = request.files['file']

        if file.filename == '':
            return 'No file selected', 400

        filename = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
        file.save(filename)
        thread = threading.Thread(target=import_data_from_file_wrapper, args=(filename, current_user.id))
        thread.start()
        session['message'] = 'File uploaded successfully! Data import in progress.'

        return redirect(url_for('dashboard'))

    return render_template('upload.html')


@app.route('/fragment/training')
@login_required
def training():
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(weeks=52)

    # Start from the Monday of the first week
    start_monday = start_date - timedelta(days=start_date.weekday())
    all_weeks = []
    current = start_monday

    while current <= end_date:
        iso_year, iso_week, _ = current.isocalendar()
        all_weeks.append((iso_year, iso_week))
        current += timedelta(weeks=1)

    # Query timestamps
    timestamps = (
        db.session.query(Series.created_at)
        .filter(Series.created_at >= start_monday)
        .all()
    )

    # Count by ISO week
    actual_counts = defaultdict(int)
    # Iterate over dates
    for dt in [ts[0] for ts in timestamps]:
        year_week = dt.isocalendar()[:2]
        actual_counts[year_week] += 1

    formatted = [
        {
            'week': f'{year}-W{week:02d}',
            'count': actual_counts.get((year, week), 0)
        }
        for (year, week) in all_weeks
    ]

    return send_file(weekly_series_plot(formatted), mimetype='image/png')


@app.route('/target/<int:series_id>')
@login_required
def target(series_id):
    series = (
        db.session.query(Series)
        .options(joinedload(Series.shot), joinedload(Series.metric))
        .filter(Series.id == series_id, Series.user_id == current_user.id)
        .first()
    )

    if not series:
        abort(404, description='Series not found')

    return send_file(generate_target(series), mimetype='image/png')


@app.route('/fragment/target/<int:series_id>')
@login_required
def fragment_target(series_id):
    series = (
        db.session.query(Series)
        .options(joinedload(Series.shot), joinedload(Series.metric))
        .filter(Series.id == series_id, Series.user_id == current_user.id)
        .first()
    )

    if not series:
        abort(404, description='Series not found')

    return render_template('fragments/target.html', series=series)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/results")
@login_required
def results():
    message = session.get('message', None)
    series = (
        db.session.query(Series)
        .filter(Series.user_id == current_user.id)
        .options(joinedload(Series.metric))
        .order_by(Series.created_at.desc())
        .limit(1000)
        .all()
    )

    return render_template("results.html", message=message, series=series)


# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        # Sanitize username to be alphanumeric only
        username = ''.join(c for c in request.form.get("username") if c.isalnum())
        password = request.form.get("password")

        if len(username) == 0 or len(password) == 0:
            return render_template("signup.html", error="Username and password cannot be empty!")

        if len(password) < 5:
            return render_template("signup.html", error="Password must be at least 5 characters long!")

        if len(username) < 3:
            return render_template("signup.html", error="Username must be at least 3 characters long!")

        if len(username) > 32:
            return render_template("signup.html", error="Username cannot exceed 32 characters!")

        if len(password) > 32:
            return render_template("signup.html", error="Password cannot exceed 32 characters!")

        if User.query.filter_by(username=username).first():
            return render_template("signup.html", error="Username already taken!")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    
    return render_template("signup.html")


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('message')
def handle_message(msg):
    print('Received message: ' + msg)
    socketio.send('Echo: ' + msg)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
