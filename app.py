from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

# In-memory storage (later replace with database)
projects = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/projects")
def project_list():
    return render_template("projects.html", projects=projects)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        link = request.form["link"]
        file = request.files["image"]

        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            projects.append({
                "title": title,
                "description": description,
                "link": link,
                "image": file.filename
            })
        return redirect(url_for("project_list"))
    return render_template("upload.html")

if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True)
