import sqlite3
import json
import os
from datetime import datetime
from models import db, Series, Shots

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


def import_ecoaims_db(db_path):
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
    
    while True:
        row = cursor.fetchone()
        if row is None:
            break

        series_id = row[0]
        data = json.loads(row[1])  # Parse JSON string into Python dict
        created_at = row[2]
        total_points = 0.0
        total_t = 0.0

        shots = extract_shots(data)
        for shot in shots:
            total_points += shot.get("points", 0.0)
            total_t += shot.get("time", 0.0)

        new_series = Series(
            id=series_id,
            created_at=datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S'),
            total_points=total_points,
            total_t=total_t
        )
        db.session.add(new_series)

        for shot in shots:
            new_shot = Shots(
                series_id=series_id,
                hit=shot.get("hit", 0),
                points=shot.get("points", 0.0),
                shotnum=shot.get("shotnum", 0),
                x=shot.get("x", 0),
                y=shot.get("y", 0),
                t=shot.get("time", 0.0)
            )
            db.session.add(new_shot)
        
        db.session.commit()
        print(f"Series ID: {series_id}, Created: {created_at}, Points: {total_points}, Time: {total_t}") 

    conn.close()


def import_data_from_file(filepath):
    # Placeholder for the actual data import logic
    print(f"Importing data from {filepath}")
    import_ecoaims_db(filepath)
    print("Data import completed.")
    os.unlink(filepath)  # Delete the file after import
    print(f"Deleted temporary file {filepath}")

