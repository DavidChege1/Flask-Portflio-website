import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- Setup ---
load_dotenv()  # loads .env at project root

app = Flask(__name__)

# Security + uploads
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(24))
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB max upload
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Admin creds (from .env)
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")  # required

# --- Helpers ---
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def require_login():
    if not session.get("logged_in"):
        return False
    return True

# --- Model ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(300), nullable=True)
    image = db.Column(db.String(300), nullable=True)

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/projects")
def project_list():
    projects = Project.query.order_by(Project.id.desc()).all()
    return render_template("projects.html", projects=projects)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not require_login():
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        link = request.form.get("link", "").strip()
        file = request.files.get("image")

        if not title:
            flash("Title is required.", "danger")
            return redirect(url_for("upload"))

        filename = None
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Invalid file type. Allowed: png, jpg, jpeg, gif, webp.", "danger")
                return redirect(url_for("upload"))
            safe_name = secure_filename(file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            file.save(file_path)
            filename = safe_name

        new_project = Project(title=title, description=description, link=link, image=filename)
        db.session.add(new_project)
        db.session.commit()
        flash("Project added.", "success")
        return redirect(url_for("project_list"))

    return render_template("upload.html")

@app.route("/edit/<int:project_id>", methods=["GET", "POST"])
def edit(project_id):
    if not require_login():
        return redirect(url_for("login"))

    project = Project.query.get_or_404(project_id)

    if request.method == "POST":
        project.title = request.form.get("title", "").strip()
        project.description = request.form.get("description", "").strip()
        project.link = request.form.get("link", "").strip()

        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Invalid file type. Allowed: png, jpg, jpeg, gif, webp.", "danger")
                return redirect(url_for("edit", project_id=project.id))
            safe_name = secure_filename(file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            file.save(file_path)
            project.image = safe_name

        if not project.title:
            flash("Title is required.", "danger")
            return redirect(url_for("edit", project_id=project.id))

        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("project_list"))

    return render_template("edit.html", project=project)

@app.route("/delete/<int:project_id>", methods=["POST"])
def delete(project_id):
    if not require_login():
        return redirect(url_for("login"))

    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "warning")
    return redirect(url_for("project_list"))

@app.route("/login", methods=["GET", "POST"])
def login():
    # Ensure hash is set
    if not ADMIN_PASSWORD_HASH:
        return "ADMIN_PASSWORD_HASH is not set in .env", 500

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["logged_in"] = True
            flash("Logged in.", "success")
            return redirect(url_for("upload"))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

# Entry
if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
