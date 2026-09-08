from fastapi import FastAPI
from Brain import handle_message
import uvicorn
import sqlite3
import json
import subprocess
from speech.TTS import speak
import time
import threading
from telegrambot import alert_user
subprocess.Popen(["python", "reminder.py"])


app = FastAPI()

def write_currentstate(currentstate):
    with open('./memory/messenger_currentstate.json','w') as f:
        f.write(json.dumps(currentstate))

conn = sqlite3.connect('./memory/messenger_logs.db',check_same_thread=False)
def save_messenger_logs(chats): #wag na isave ang 'unread' ala kwinta
    for chat in chats:
        values = (
            chat.get("thread_id"),
            chat.get("thread_name"),
            chat.get("sender"),
            chat.get("content"),
            chat.get("is_group"),
            chat.get("timestamp")
        )

        conn.execute("""
        INSERT INTO messages 
        (thread_id, thread_name, sender,content, is_group, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, values)

    conn.commit()

@app.post("/message")
def message(data: dict):
    time1 = time.perf_counter()
    response = handle_message(data.get("content"))
    threading.Thread(target=speak, args=(response,), daemon=True).start()
    print("\ngeneration time:", time.perf_counter()-time1)
    return {"reply": response}

@app.post("/event")
def event(data: dict):
    source = data.get("source")

    if source == "messenger":
        write_currentstate(data.get("currentstate"))
        save_messenger_logs(data["chats"])

    elif source == "reminder":
        response = handle_message(data.get("content"))
        alert_user(response)
        
    else:
        print(f"no source named: {data.get("source")}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)