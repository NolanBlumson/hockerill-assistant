from flask import Flask, request, jsonify, send_file
from openai import OpenAI
import os
import time

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_ID = "asst_rLUFKlCP4X5Tt0dii1WuLfEI"

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")
    thread_id = data.get("thread_id", None)

    if not question:
        return jsonify({"answer": "Please provide a question."}), 400

    # Create a new thread if none exists
    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
    else:
        thread = client.beta.threads.retrieve(thread_id=thread_id)

    # Add user message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )

    # Run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # Wait for completion
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled", "expired"]:
            return jsonify({"answer": f"Assistant failed with status: {run_status.status}"}), 500
        time.sleep(1)

    # Retrieve assistant reply
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value.strip()

    return jsonify({
        "answer": answer,
        "thread_id": thread_id
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
