import os 
import csv
import json
import requests
from flask import Flask, render_template, request
import weaviate

app = Flask("app")

def safe_filename(filename):
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")

    return filename


def call_llm(message):
    """
    Genos LLM 호출하는 함수
    """
    serving_id = 43
    bearer_token = 'b37080c0a4f747d9978f8bd1c4f6ecce'

    url = f"https://genos.genon.ai:3443/api/gateway/{serving_id}"
    headers = dict(Authorization=f"Bearer {bearer_token}")
    endpoint = f"{url}/v1/chat/completions"

    response = requests.post(endpoint, headers=headers, json={"messages": [{"role": "user", "content": message}]})
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return None


# main window
@app.route("/")
def home():
    return render_template("main_window.html", service_name="Omni-Agent")
        

@app.route("/send_message", methods=["POST"])
def return_message():
    """
    사용자가 보낸 메시지를 LLM에 전송하고, 그 응답을 대화 이력에 추가하고, 응답을 return
    """
    # 1. 외부 LLM에 사용자가 보낸 메시지를 전송
    user_message = request.form["chat_text"]
    response = call_llm(user_message)

    # 2. 외부 LLM으로부터 받은 응답을 기존 대화 DB에 추가하여 저장
    chat_history_db_path = "conv_db/chat_history.csv"
    chat_history = []
    if os.path.exists(chat_history_db_path):
        with open(chat_history_db_path, "r") as f:
            chat_history = list(csv.reader(f))

    if not chat_history:
        chat_history = []
        chat_history.append(["role", "message"])

    chat_history.append(["user", user_message])
    chat_history.append(["model", response])

    with open(chat_history_db_path, "w") as f:
        csv.writer(f).writerows(chat_history)

    # 3. 해당 history를 return
    return render_template("main_window.html", history=chat_history[1:]) # 0번 row는 header이므로 제외


# upsert docs
@app.route("/upsert_docs")
def upsert_docs():
    return render_template("upsert_docs.html")


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
        return render_template("upsert_docs.html", filenames=filenames)
    

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
            return render_template("upsert_docs.html", db_error=db_response.errors)
        else:
            return render_template("upsert_docs.html", db_error="success")


app.run("0.0.0.0", port=10800, debug=True)