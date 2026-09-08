import sqlite3
import numpy as np
from fastembed import TextEmbedding

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def save_memory(content, date_str):
    vector = list(embedding_model.embed([content]))[0]
    vec_blob = vector.astype(np.float32).tobytes()

    conn = sqlite3.connect("memory/semantic.db")
    conn.execute(
        "INSERT INTO memories (content, date_sent, embedding) VALUES (?, ?, ?)",
        (content, date_str, vec_blob)
    )
    conn.commit()
    conn.close()



def retrieve_memory(user_query, top_k=3,score_val=0.6):
    query_vector = list(embedding_model.embed([user_query]))[0].astype(np.float32)
    
    conn = sqlite3.connect("memory/semantic.db")
    rows = conn.execute("SELECT content, date_sent, embedding FROM memories").fetchall()
    conn.close()

    matches = []
    for content, date_sent, vec_blob in rows:
        mem_vec = np.frombuffer(vec_blob, dtype=np.float32)
        score = np.dot(query_vector, mem_vec) / (np.linalg.norm(query_vector) * np.linalg.norm(mem_vec))

        if score > score_val:
            matches.append({"content":content, "date_sent": date_sent, "score": score})
        
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:top_k]