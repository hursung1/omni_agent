import os 
import json
from flask import Flask, render_template, request
import weaviate

app = Flask("app")

def safe_filename(filename):
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")

    return filename


@app.route("/")
def home():
    return render_template("index.html", service_name="aaa")

@app.route("/upload", methods=["POST"])
def upload_files():
    if request.method == "POST":
        files = request.files.getlist("file")
        return_msg = "<ul>"
        filenames = []

        for f in files:
            filename = safe_filename(f.filename)
            f.save("./file/"+filename)
            filenames.append(filename)
        
        # os.listdir
        return render_template("index.html", filenames=filenames)
    

@app.route("/db_upload", methods=["POST"])
def weaviate_upload():
    if request.method == "POST":
        db_index = request.form["text"]
        client = weaviate.connect_to_local()
        db = client.collections.get(db_index) ## collection 이름 받아와야 함
        
        file_list = os.listdir("./file")
        data = []
        for file in file_list:
            if not file.endswith(".json"): continue
            with open(f"./file/{file}", "r", encoding="UTF-8") as f:
                data.extend(json.load(f)) 

        print(data)
        db_response = db.data.insert_many(data)
        client.close()

        if db_response.has_errors:
            return render_template("index.html", db_error=db_response.errors)
        else:
            return render_template("index.html", db_error="success")
        
# @app.route("/file_select", methods=["POST"])
# def show_selected_files():
#     request.

app.run("0.0.0.0", port=10800, debug=True)