from collections import defaultdict
from datetime import datetime, timedelta, timezone
import threading
import uuid
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import joinedload
from data_importer import import_data_from_file
from models import db, Series, User
from plots import weekly_series_plot, generate_target, median_points
from metrics import compute_metrics
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import abort, session, send_file
from flask import Flask, render_template, request, redirect, url_for, copy_current_request_context, jsonify


# TODO: timezone should be in user configuration
def localize_timestamp(ts):
    # Ensure the timestamp is timezone-aware UTC, then convert to local time
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    # FIXME: timezone is user-specific
    return ts.astimezone()  # convert to system local timezone


def localize_timestamps(series):
    for s in series:
        s.created_at = localize_timestamp(getattr(s, "created_at"))


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
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', str(uuid.uuid4()))

    # Initialize the Flask-SQLAlchemy extension
    db.init_app(app)

    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()

    return app


app = create_app()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/data', methods=['GET'])
@login_required
def get_heatmap_data():
    series = (
        db.session.query(Series)
        .filter(Series.user_id == current_user.id)
        .order_by(Series.created_at.asc())
        .with_entities(
            func.date(Series.created_at).label('date'),
            func.count(Series.id).label('value')
        ).group_by(func.date(Series.created_at)).order_by(func.date(Series.created_at).asc())
        .all()
    )

    if not series:
        abort(404, description='No series found')

    return jsonify([{'date': str(row.date), 'value': row.value} for row in series])


@app.route('/data/series', methods=['GET'])
@login_required
def data_series():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 100, type=int)
    offset = (page - 1) * limit

    # Get total count
    total = db.session.query(func.count(Series.id)).filter(
        Series.user_id == current_user.id).scalar()

    # Get paginated results
    series = (
        db.session.query(Series)
        .options(joinedload(Series.metric))
        .filter(Series.user_id == current_user.id)
        .order_by(Series.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not series and total > 0:
        abort(404, description='Page not found')

    return jsonify({
        'totalItems': total,
        'items': [{
            'id': s.id,
            'created_at': localize_timestamp(s.created_at).strftime('%Y-%m-%d %H:%M'),
            'description': s.description,
            'total_points': round(s.total_points, 1),
            'total_t': round(s.total_t, 1),
            'consistency': round(next((m.value for m in s.metric if m.name == 'ConsistencyPct'), 0), 1)
        } for s in series]})


@app.route('/series', methods=['GET'])
@login_required
def get_series():
    return render_template('series.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    @copy_current_request_context
    def import_data_from_file_wrapper(filename, user_id):
        import_data_from_file(filename, user_id)

    if request.method == "POST":
        if 'file' not in request.files:
            return 'No file part in the request', 400

        file = request.files['file']

        if file.filename == '':
            return 'No file selected', 400

        filename = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
        file.save(filename)
        thread = threading.Thread(
            target=import_data_from_file_wrapper, args=(filename, current_user.id))
        thread.start()

        return redirect(url_for('dashboard'))

    return render_template('upload.html')


@app.route('/report/series/weekly_count')
@login_required
def report_series_weekly_count():
    return render_template('report_series_weekly_count.html')


# TODO: choose the right metric and time aggregation
@app.route('/report/series/median_points', methods=['GET'])
@login_required
def report_series_median_points():
    series = (
        db.session.query(Series)
        .options(joinedload(Series.shot))
        .filter(Series.user_id == current_user.id)
        .order_by(Series.created_at.asc())
        .all()
    )

    if not series:
        abort(404, description='No series found')

    return render_template("report_series_median_points.html", data=median_points(series))


# It is unfeasible to do this in database-agnostic way, therefore most part is done with Python.
@app.route('/data/series/weekly_count')
@login_required
def data_series_weekly_count():
    end_date = localize_timestamp(datetime.utcnow())
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
    # Convert the local start_monday back to UTC for querying the DB (DB timestamps are in UTC)
    start_monday_utc = start_monday.astimezone(timezone.utc)
    # TODO: If the DB stores tz-aware datetimes, pass start_monday_utc instead.
    start_monday_for_query = start_monday_utc.replace(tzinfo=None)

    timestamps = (
        db.session.query(Series.created_at)
        .filter(Series.created_at >= start_monday_for_query, Series.user_id == current_user.id)
        .all()
    )

    # Count by ISO week
    actual_counts = defaultdict(int)
    # Iterate over dates
    for dt in [localize_timestamp(ts[0]) for ts in timestamps]:
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


# TODO: fragment (?)
@app.route('/report/series/latest_date')
@login_required
def report_series_latest_date():
    latest_date = (
        db.session.query(func.max(Series.created_at))
        .filter(Series.user_id == current_user.id)
        .scalar()
    ).date()
    # TODO: this could be SQLite specific (?)
    series = (
        db.session.query(Series)
        .options(joinedload(Series.shot), joinedload(Series.metric))
        .filter(
            func.date(Series.created_at) == latest_date,
            Series.user_id == current_user.id
        )
        .all()
    )

    shots = [[shot.x, shot.y] for s in series for shot in s.shot]
    metrics = compute_metrics(shots)

    return render_template('latest_date.html', date=latest_date, shots=shots, metrics=metrics)


@app.route('/fragment/multiseries/<date>')
@login_required
def fragment_multiseries_date(date):
    # TODO: this could be SQLite specific (?)
    series = (
        db.session.query(Series)
        .options(joinedload(Series.shot), joinedload(Series.metric))
        .filter(
            func.date(Series.created_at) == date,
            Series.user_id == current_user.id
        )
        .all()
    )

    shots = [[shot.x, shot.y] for s in series for shot in s.shot]
    metrics = compute_metrics(shots)

    return render_template('fragments/multiseries.html', date=date, shots=shots, metrics=metrics)


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

    localize_timestamps([series])

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

    localize_timestamps([series])

    return render_template('fragments/target.html', series=series)


@app.route("/dashboard")
@login_required
def dashboard():
    series_count = db.session.query(
        func.count(Series.id)).filter(Series.user_id == current_user.id).scalar()
    params = {
        "series_count": series_count
    }

    return render_template("dashboard.html", params=params)


@app.route('/results')
@login_required
def results():
    series = (
        db.session.query(Series)
        .filter(Series.user_id == current_user.id)
        .options(joinedload(Series.metric))
        .order_by(Series.created_at.desc())
        .limit(1000)
        .all()
    )

    localize_timestamps(series)

    return render_template('results.html', series=series)


# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        # Sanitize username to be alphanumeric only
        username = ''.join(c for c in request.form.get(
            "username") if c.isalnum())
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

        hashed_password = generate_password_hash(
            password, method="pbkdf2:sha256")

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


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
