from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

app = Flask("app")

@app.route("/")
def home():
    return render_template("index.html", service_name="aaa")

@app.route("/", methods=["POST"])
def upload_files():
    f = request.files["file"]
    f.save("./file/"+secure_filename(f.filename))
    return "done"

app.run("0.0.0.0", port=10800, debug=True)