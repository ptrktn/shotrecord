import sqlite3
import json
import os
from datetime import datetime
from models import db, Series, Shots


def population_variance(data):
    """Calculate the population variance of a list of numbers."""
    if len(data) == 0:
        return 0.0
    mean = sum(data) / len(data)
    return sum((x - mean) ** 2 for x in data) / len(data)


# Recursive function to find all "shot" elements
# FIXME: this is duplicated in cli.py
def extract_shots(obj):
    shots = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "shot":
                shots.append(value)
            else:
                shots.extend(extract_shots(value))
    elif isinstance(obj, list):
        for item in obj:
            shots.extend(extract_shots(item))
    return shots


# FIXME: coordinate transformation not handled here
def import_ecoaims_db(db_path, user_id):
    """Import data from an Ecoaims SQLite database file.
    sqlite> .schema ekoaims_games
        CREATE TABLE ekoaims_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game TEXT NOT NULL,
            settings TEXT NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, game, created FROM ekoaims_games ORDER BY id ASC")
    
    n_skipped = 0

    while True:
        row = cursor.fetchone()
        if row is None:
            break

        source_id = row[0]
        data = json.loads(row[1])  # Parse JSON string into Python dict
        created_at = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
        total_points = 0.0
        total_t = 0.0

        # Check if this series already exists to avoid duplicates (good enough for now)
        if Series.query.filter_by(user_id=user_id, created_at=created_at).first():
            n_skipped += 1
            continue

        shots = extract_shots(data)
        for shot in shots:
            total_points += shot.get("points", 0.0)
            total_t += shot.get("time", 0.0)

        series = Series(
            user_id=user_id,
            source_id=source_id,
            created_at=created_at,
            total_points=total_points,
            total_t=total_t,
            n=len(shots),
            variance=population_variance([shot.get("points", 0.0) for shot in shots])
        )
        db.session.add(series)
        db.session.flush()  # Get the ID assigned by the database
        series_id = series.id

        for shot in shots:
            new_shot = Shots(
                series_id=series_id,
                hit=shot.get("hit", 0),
                points=shot.get("points", 0.0),
                shotnum=shot.get("shotNumber", 0),
                x=shot.get("x", 0),
                y=shot.get("y", 0),
                t=shot.get("time", 0.0)
            )
            db.session.add(new_shot)
        
        db.session.commit()
        print(f"User ID: {user_id}, Series ID: {series_id}, Created: {created_at}, Points: {total_points}, Time: {total_t}")

    conn.close()

    print(f"User ID {user_id} import completed, skipped {n_skipped} existing series")


# FIXME: currently only imports Ecoaims DBs
def import_data_from_file(filepath, user_id):
    # Placeholder for the actual data import logic
    print(f"Importing user ID {user_id} data from {filepath}")
    import_ecoaims_db(filepath, user_id)
    print("Data import completed")
    os.unlink(filepath)  # Delete the file after import
    print(f"Deleted temporary file {filepath}")

