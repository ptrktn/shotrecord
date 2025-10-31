#!/usr/bin/env python3

import sqlite3
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import argparse

debug = False


def plot_shots(coordinates, filename="shot_coordinates.png", xcal=-20, ycal=10):
    """
    Plot each (x, y) coordinate as a circle and mark the center point.
    Saves the result as an image file.

    Parameters:
        coordinates (list of tuple): List of (x, y) coordinates.
        filename (str): Output image filename (default: 'shot_coordinates.png').
    """
    if not coordinates:
        raise ValueError("The coordinates list is empty.")

    # Create the plot
    fig, ax = plt.subplots(figsize=(6, 6))
    n = 11
    xscale = 2.2
    ring = Circle((300, 250), radius=int(0.5 * 59.5 * xscale),
                  fill=True, facecolor='black', edgecolor='black', linewidth=1)
    ax.add_patch(ring)

    for i in [5, 11.5, 27.5, 43.5, 59.5, 75.5, 91.5, 107.5, 123.5, 139.5, 155.5]:
        if n > 7:
            edgecolor = 'white'
        else:
            edgecolor = 'black'

        ring = Circle((300, 250), radius=int(0.5 * i * xscale),
                      fill=False, edgecolor=edgecolor, linewidth=1)
        ax.add_patch(ring)
        n -= 1

    # ax.axline((0,250), (600,250), color='black', linewidth=1)
    # ax.axline((300,0), (300,500), color='black', linewidth=1)
    # Plot each coordinate as a circle
    num = 0
    for (x, y) in coordinates:
        num += 1
        circle = Circle((x + xcal, y + ycal), radius=9, fill=True,
                        facecolor='yellow', edgecolor='black', linewidth=1)
        ax.add_patch(circle)
        ax.annotate(str(num), (x + xcal, y + ycal), color='blue',
                    fontsize=7, ha='center', va='center')

    ax.set_xlim(0, 600)
    ax.set_ylim(0, 500)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title("ShotRecord Shot Plot")
    ax.axes.invert_yaxis()  # Invert y-axis to match coordinate system
    ax.axis('off')  # Turn off the axis

    # Save the figure instead of showing it
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


# Recursive function to find all "shot" elements
def extract_shots(obj):
    shots = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "shot":
                if value is not False:
                    shots.append(value)
            else:
                shots.extend(extract_shots(value))
    elif isinstance(obj, list):
        for item in obj:
            shots.extend(extract_shots(item))
    return shots


def handle_ecoaims_db(db_path, game_id=None):
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

    if game_id:
        cursor.execute("SELECT * FROM ekoaims_games WHERE id = ?", (game_id,))
    else:
        cursor.execute("SELECT * FROM ekoaims_games ORDER BY created DESC")

    while True:
        row = cursor.fetchone()
        if row is None:
            break

        data = json.loads(row[1])  # Parse JSON string into Python dict

        if debug:
            print("ID: {row[0]} Created: {row[3]}")
            print("Data:")
            print(json.dumps(data, indent=4))
            print("Settings:")
            print(json.dumps(json.loads(row[2]), indent=4))

        coords = []
        all_shots = extract_shots(data)
        for shot in all_shots:
            # shot: false
            # if shot == False:
            #    continue

            # print(json.dumps(shot, indent=4))
            coords.append((shot["x"], shot["y"]))

        plot_shots(coords, filename=f"shotrecord_{row[0]:05d}.png")

    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create shot plots')
    parser.add_argument('--game_id', type=int, required=False,
                        help='Ecoaims ID of the game to plot shots for')
    parser.add_argument('--ecoaims_db', type=str, required=True,
                        help='Path to Ecoaims SQLite database file')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    args = parser.parse_args()
    debug = args.debug

    if args.ecoaims_db:
        handle_ecoaims_db(args.ecoaims_db, game_id=args.game_id)
