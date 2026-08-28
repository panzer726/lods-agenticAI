from fastapi import FastAPI
from Brain import handle_message
import uvicorn
import sqlite3
import json

app = FastAPI()

def write_currentstate(currentstate):
    with open('./memory/messenger_currentstate.json','w') as f:
        f.write(json.dumps(currentstate))

conn = sqlite3.connect('./memory/messenger_logs.db',check_same_thread=False)
def save_messenger_logs(chats): #wag na isave ang 'unread' ala kwinta
    for chat in chats:
        thread_id,thread_name,sender = chat.get('thread_id'),chat.get('thread_name'),chat.get('sender')
        content,is_group,timestamp = chat.get('content'),chat.get('is_group'),chat.get('timestamp')

        conn.execute("""
        INSERT INTO messages (thread_id,thread_name,sender,content,is_group,timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,(
        thread_id, thread_name, sender, content, is_group, timestamp
        ))
        conn.commit()

@app.post("/message")
def message(data: dict):
    source = data.get("source")   # "discord", "terminal", "messenger"
    content = data.get("content")
    
    response = handle_message(content)
    return {"reply": response}

@app.post("/event")
def event(data: dict):
    if data.get("source")=="messenger":
        write_currentstate(data.get("currentstate"))
        save_messenger_logs(data["chats"])
    else:
        print(f"no source named: {data.get("source")}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)