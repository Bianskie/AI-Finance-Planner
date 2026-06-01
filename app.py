from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai
import db_manager
import json
import os
import vector_db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Konfigurasi Folder Upload
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Konfigurasi AI 
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ------
# 1. UI
# ------
@app.route('/')
def index():
    return render_template('index.html')

# ------
# 2. CRUD
# ------
@app.route('/api/get_transactions', methods=['GET'])
def get_transactions():
    data = db_manager.get_all_transactions()
    return jsonify(data)

@app.route('/api/add_transaction', methods=['POST'])
def add_transaction():
    data = request.json
    db_manager.add_transaction(
        category=data['category'],
        trans_type=data['type'],
        amount=int(data['amount']),
        date=data['date']
    )
    return jsonify({"status": "success"})

@app.route('/api/delete_transaction/<int:trx_id>', methods=['DELETE'])
def delete_transaction(trx_id):
    db_manager.delete_transaction(trx_id)
    return jsonify({"status": "success"})

# ------
# 3. Rute Savings Goal
# ------
GOAL_FILE = 'goal.json'

@app.route('/api/get_goal', methods=['GET'])
def get_goal():
    if os.path.exists(GOAL_FILE):
        with open(GOAL_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({"goal": 0})

@app.route('/api/set_goal', methods=['POST'])
def set_goal():
    data = request.json
    with open(GOAL_FILE, 'w') as f:
        json.dump({"goal": int(data['goal'])}, f)
    return jsonify({"status": "success"})

# ------
# 4. Rute Chatbot
# ------
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_message = request.form.get('message', '')
        file = request.files.get('file')
        
        extracted_text = ""
        # List untuk menampung gambar dan teks langsung ke AI
        contents_to_send = [] 
        
        # ------
        # 1. Ambil data tabular dari dashboard (database.json)
        # ------
        try:
            financial_data = db_manager.get_all_transactions()
        except:
            financial_data = "Data transaksi kosong."

        # ------
        # 2. Proses file gambar
        # ------
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            image_file = genai.upload_file(filepath)
            contents_to_send.append(image_file) 
            
            # Coba ekstrak teks untuk disimpan ke memori (Vector)
            try:
                vision_prompt = "Ekstrak nama tempat dan total harga dari struk ini. Singkat saja."
                vision_resp = model.generate_content([vision_prompt, image_file])
                extracted_text = vision_resp.text.strip()
            except:
                pass 

        # ------
        # 3. Menyimpan ke memory.json
        # ------
        if extracted_text:
            try: 
                vector_db.save_memory(f"Informasi Struk: {extracted_text}")
                print(f"SUKSES: Teks struk berhasil di-embed!")
            except Exception as e: 
                print(f"GAGAL SIMPAN STRUK KE VEKTOR: {str(e)}")
            
        if user_message:
            try: 
                vector_db.save_memory(f"User berkata: {user_message}")
                print(f"SUKSES: Pesan user berhasil di-embed!")
            except Exception as e: 
                print(f"GAGAL SIMPAN CHAT KE VEKTOR: {str(e)}")

        # ------
        # 4. Retrieve, mencari ingatan
        # ------
        relevant_memory = vector_db.search_memory(user_message)
        
        # ------
        # 5. Prompt lengkap
        # ------
        prompt = f"""
        You are an AI Finance Assistant.
        
        [1] USER'S ACTUAL FINANCIAL DATA (Database Dashboard):
        {json.dumps(financial_data)}
        
        [2] RELEVANT PAST MEMORIES (Vector Chat History):
        {relevant_memory}
        
        [3] USER'S CURRENT MESSAGE:
        {user_message}
        
        INSTRUCTIONS:
        - Please answer based on ALL the context provided above.
        - If the user asks about their income, balance, or expenses, CALCULATE IT carefully from the FINANCIAL DATA [1].
        - If the user uploaded a receipt image just now, analyze it and give advice.
        """
        contents_to_send.append(prompt)
        
        # ------
        # 6. Hasilkan jawaban
        # ------
        response = model.generate_content(contents_to_send)
        return jsonify({"response": response.text})
        
    except Exception as e:
        return jsonify({"response": f"**System Error:** {str(e)}"})
    
# ------
# 5. Jalankan Server
# ------
if __name__ == '__main__':
    app.run(debug=True)