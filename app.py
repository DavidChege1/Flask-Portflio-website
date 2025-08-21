# Planning to add security options
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SECRET_KEY"] = "supersecretkey"  # change this!
db = SQLAlchemy(app)

# Database model
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(200), nullable=True)

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Projects list
@app.route("/projects")
def project_list():
    projects = Project.query.all()
    return render_template("projects.html", projects=projects)

# Upload (protected)
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        link = request.form["link"]
        file = request.files["image"]

        filename = None
        if file:
            filename = file.filename
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

        new_project = Project(title=title, description=description, link=link, image=filename)
        db.session.add(new_project)
        db.session.commit()

        return redirect(url_for("project_list"))

    return render_template("upload.html")

# Edit project
@app.route("/edit/<int:project_id>", methods=["GET", "POST"])
def edit(project_id):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    project = Project.query.get_or_404(project_id)

    if request.method == "POST":
        project.title = request.form["title"]
        project.description = request.form["description"]
        project.link = request.form["link"]

        file = request.files["image"]
        if file:
            filename = file.filename
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            project.image = filename

        db.session.commit()
        return redirect(url_for("project_list"))

    return render_template("edit.html", project=project)

# Delete project
@app.route("/delete/<int:project_id>", methods=["POST"])
def delete(project_id):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for("project_list"))

# Simple login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Replace with your own username/password
        if username == "admin" and password == "password":
            session["logged_in"] = True
            return redirect(url_for("upload"))
        else:
            return "Invalid credentials. Try again."

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
