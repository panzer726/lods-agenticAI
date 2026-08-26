import sqlite3
import numpy as np
from fastembed import TextEmbedding

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def save_memory(content, date_str):
    vector = list(embedding_model.embed([content]))[0]
    vec_blob = vector.astype(np.float32).tobytes()

    conn = sqlite3.connect("memory/long_term.db")
    conn.execute(
        "INSERT INTO memories (content, date_sent, embedding) VALUES (?, ?, ?)",
        (content, date_str, vec_blob)
    )
    conn.commit()
    conn.close()


def retrieve_memory(user_query, top_k=3,score_val=0.6,withdate=True):
    query_vector = list(embedding_model.embed([user_query]))[0].astype(np.float32)
    
    conn = sqlite3.connect("memory/long_term.db")
    rows = conn.execute("SELECT content, date_sent, embedding FROM memories").fetchall()
    conn.close()
    
    if not rows:
        return ""
        
    scored = []
    for content, date_sent, vec_blob in rows:
        mem_vec = np.frombuffer(vec_blob, dtype=np.float32)
        score = np.dot(query_vector, mem_vec) / (np.linalg.norm(query_vector) * np.linalg.norm(mem_vec))
        scored.append((score, content, date_sent))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    
    memory_block = ""
    for score, content, date_sent in scored[:top_k]:
        if score > score_val: 
            memory_block += f"- {content.split("|")[0]} {date_sent}\n"

    return memory_block
