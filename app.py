from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "albums.db"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads" / "album-covers"

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["DATABASE_URL"] = os.environ.get("DATABASE_URL")


def ensure_upload_folder() -> None:
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def get_db_connection() -> sqlite3.Connection:
    if app.config["DATABASE_URL"]:
        connection = sqlite3.connect(app.config["DATABASE_URL"])
    else:
        connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                cover_image TEXT
            )
            """
        )
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(albums)").fetchall()
        }
        if "cover_image" not in columns:
            connection.execute("ALTER TABLE albums ADD COLUMN cover_image TEXT")
        connection.commit()


def seed_albums() -> None:
    with get_db_connection() as connection:
        existing = connection.execute("SELECT COUNT(*) AS count FROM albums").fetchone()["count"]
        if existing:
            return

        now = datetime.now(timezone.utc).isoformat()
        connection.executemany(
            "INSERT INTO albums (name, created_at) VALUES (?, ?)",
            [
                ("Summer 2024", now),
                ("Travels", now),
            ],
        )
        connection.commit()


init_db()
seed_albums()
ensure_upload_folder()


@app.route("/")
def index() -> str:
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/create-album.html")
def create_album_page() -> str:
    return send_from_directory(BASE_DIR, "create-album.html")


@app.route("/api/albums", methods=["GET", "POST"])
def albums_api():
    if request.method == "POST":
        payload = request.form if request.form else (request.get_json(silent=True) or {})
        name = str(payload.get("name", payload.get("album-name", ""))).strip()

        if not name:
            return jsonify({"error": "Album name is required."}), 400

        cover_image = None
        cover_file = request.files.get("cover-image")
        if cover_file and cover_file.filename:
            original_name = secure_filename(cover_file.filename)
            suffix = Path(original_name).suffix.lower()
            generated_name = f"{uuid.uuid4().hex}{suffix}"
            relative_path = Path("uploads") / "album-covers" / generated_name
            cover_file.save(UPLOAD_FOLDER / generated_name)
            cover_image = relative_path.as_posix()

        created_at = datetime.now(timezone.utc).isoformat()
        try:
            with get_db_connection() as connection:
                cursor = connection.execute(
                    "INSERT INTO albums (name, created_at, cover_image) VALUES (?, ?, ?)",
                    (name, created_at, cover_image),
                )
                connection.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "An album with that name already exists."}), 409

        return jsonify(
            {
                "id": cursor.lastrowid,
                "name": name,
                "created_at": created_at,
                "cover_image": cover_image,
                "cover_url": f"/static/{cover_image}" if cover_image else None,
            }
        ), 201

    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, created_at, cover_image FROM albums ORDER BY created_at DESC, id DESC"
        ).fetchall()

    albums = []
    for row in rows:
        album = dict(row)
        cover_image = album.get("cover_image")
        album["cover_url"] = f"/static/{cover_image}" if cover_image else None
        albums.append(album)

    return jsonify(albums)


if __name__ == "__main__":
    app.run(debug=True)