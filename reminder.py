import sqlite3
import time
import requests

conn = sqlite3.connect("memory/reminders.db", timeout=5)
conn.execute("PRAGMA journal_mode=WAL;")

while True:
    cur = conn.cursor()
    cur.execute("""
        SELECT id, content FROM reminders 
        WHERE trigger_time <= ?
    """, (int(time.time()),))
    
    due_reminders = cur.fetchall()

    for id, content in due_reminders:
        success = requests.post("http://localhost:8000/event",json={"source":"reminder","content":f"(A reminder is due: {content}. Speak this to the user in a short natural sentence.)" })

        if success:
            cur.execute("DELETE FROM reminders WHERE id = ?", (id,))
            conn.commit()

    cur.close()
    time.sleep(1)
