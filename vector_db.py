import google.generativeai as genai
import numpy as np
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MEMORY_FILE = 'memory.json'

def get_embedding(text):
    result = genai.embed_content(
        model="models/gemini-embedding-001", 
        content=text
    )
    return result['embedding']

def cosine_similarity(vec1, vec2):
    # Pelindung pembagian dengan nol
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0: return 0.0
    dot_product = np.dot(vec1, vec2)
    return dot_product / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def save_memory(text_content):
    vector = get_embedding(text_content)
    memory_db = []
    
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory_db = json.load(f)
        except:
            memory_db = []
            
    memory_db.append({"text": text_content, "embedding": vector})
    
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory_db, f)

def search_memory(query_text, top_k=3):
    if not os.path.exists(MEMORY_FILE):
        return "Belum ada ingatan masa lalu yang tersimpan."
        
    try:
        with open(MEMORY_FILE, 'r') as f:
            memory_db = json.load(f)
    except:
        return "Belum ada ingatan masa lalu yang tersimpan."
        
    if not memory_db:
        return "Belum ada ingatan masa lalu yang tersimpan."
        
    query_vector = get_embedding(query_text)
    for item in memory_db:
        item['score'] = cosine_similarity(query_vector, item['embedding'])
        
    memory_db.sort(key=lambda x: x['score'], reverse=True)
    top_results = [item['text'] for item in memory_db[:top_k]]
    return "\n---\n".join(top_results)