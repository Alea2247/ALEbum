from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import random
import string
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "macickaklucik"

# CONFIG
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_aXE9B6CnhDRF@ep-empty-shadow-alwwazrt-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

# ensure uploads folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# =========================
# MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    invite_code = db.Column(db.String(10), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class AlbumUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey("album.id"), nullable=False)


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey("album.id"), nullable=False)


# =========================
# HELPERS
# =========================

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def login_required():
    if "user_id" not in session:
        return False
    return True


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    if "user_id" in session:
        return render_template("home.html", username=session["username"])
    return render_template("index.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        # log the user in immediately after registration
        session["user_id"] = new_user.id
        session["username"] = new_user.username

        return redirect(url_for("home"))

    return render_template("register.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("home"))

        return "Zlé meno alebo heslo"

    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- CREATE ALBUM ----------
@app.route("/create-album", methods=["GET", "POST"])
def create_album():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        code = generate_code()

        album = Album(
            name=name,
            invite_code=code,
            created_by=session["user_id"]
        )

        db.session.add(album)
        db.session.commit()

        link = AlbumUser(
            user_id=session["user_id"],
            album_id=album.id
        )

        db.session.add(link)
        db.session.commit()

        return f"Album vytvorený! Kód: {code}"

    return render_template("create_album.html")


# ---------- JOIN ALBUM ----------
@app.route("/join-album", methods=["GET", "POST"])
def join_album():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        code = request.form["code"]

        album = Album.query.filter_by(invite_code=code).first()

        if not album:
            return "Album neexistuje"

        exists = AlbumUser.query.filter_by(
            user_id=session["user_id"],
            album_id=album.id
        ).first()

        if exists:
            return "Už si v albume"

        link = AlbumUser(
            user_id=session["user_id"],
            album_id=album.id
        )

        db.session.add(link)
        db.session.commit()

        return "Pridaná do albumu 💕"

    return render_template("join_album.html")


# ---------- UPLOAD PHOTO ----------
@app.route("/upload/<int:album_id>", methods=["GET", "POST"])
def upload(album_id):
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["image"]
        description = request.form["description"]

        if file:
            filename = f"{random.randint(1000,9999)}_{secure_filename(file.filename)}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            photo = Photo(
                filename=filename,
                description=description,
                user_id=session["user_id"],
                album_id=album_id
            )

            db.session.add(photo)
            db.session.commit()

            return "Foto uložené 💕"

    return render_template("upload.html", album_id=album_id)


# ---------- VIEW ALBUM ----------
@app.route("/album/<int:album_id>")
def album(album_id):
    if not login_required():
        return redirect(url_for("login"))

    photos = Photo.query.filter_by(album_id=album_id).order_by(Photo.created_at.desc()).all()
    return render_template("album.html", photos=photos)


# ---------- SERVE IMAGES ----------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)