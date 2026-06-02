from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai
import db_manager
import json
import os
import time
from datetime import datetime
import vector_db
from dotenv import load_dotenv
from PIL import Image 

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

# Mematikan sistem keamanan
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

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
        category=data['category'].title(),
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
        user_message = ""
        file = None
        
        if request.is_json:
            user_message = request.json.get('message', '')
        else:
            user_message = request.form.get('message', '')
            file = request.files.get('file')
            
        extracted_text = ""
        contents_to_send = [] 
        
        # ------
        # 1. Proses file gambar / PDF 
        # ------
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Cek Ekstensi File
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            media_for_ai = None
            
            try:
                if ext in ['png', 'jpg', 'jpeg', 'webp']:
                    # JIKA GAMBAR: Langsung buka di lokal pakai PIL, TIDAK DIUPLOAD KE GOOGLE STORAGE
                    media_for_ai = Image.open(filepath)
                else:
                    # JIKA PDF: Wajib pakai Google File Storage
                    uploaded_file = genai.upload_file(filepath)
                    while uploaded_file.state.name == "PROCESSING":
                        time.sleep(2)
                        uploaded_file = genai.get_file(uploaded_file.name)
                        
                    if uploaded_file.state.name == "FAILED":
                        raise Exception("Google gagal memproses PDF ini.")
                    media_for_ai = uploaded_file
                    
                contents_to_send.append(media_for_ai) 
                
                extract_prompt = "Extract the place name (category) and the total price from this receipt or document.\n"
                extract_prompt += "Respond ONLY with a valid JSON exactly like this format:\n"
                extract_prompt += '{"category": "Place Name", "amount": 15000}\n'
                extract_prompt += "Ensure the amount is just an integer without currency symbols.\n"
                extract_prompt += "If it is NOT a receipt, return an empty JSON: {}"
                
                extract_resp = model.generate_content(
                    [extract_prompt, media_for_ai],
                    safety_settings=SAFETY_SETTINGS
                )
                
                clean_json = extract_resp.text.replace('```json', '').replace('```', '').strip()
                
                if clean_json and clean_json != "{}":
                    receipt_data = json.loads(clean_json)
                    if 'category' in receipt_data and 'amount' in receipt_data:
                        db_manager.add_transaction(
                            category=str(receipt_data['category']).title(),
                            trans_type="Expense",
                            amount=int(receipt_data['amount']),
                            date=datetime.now().strftime("%Y-%m-%d")
                        )
                        extracted_text = "System Info: A file from " + str(receipt_data['category'])
                        extracted_text += " for Rp" + str(receipt_data['amount']) + " was automatically added to the Database."
                
            except Exception as e:
                print("INFO: Gagal ekstrak ke DB. Detail: " + str(e))

        # ------
        # 2. Ambil data tabular dari dashboard
        # ------
        try:
            financial_data = db_manager.get_all_transactions()
        except Exception:
            financial_data = "Data transaksi kosong."

        # ------
        # 3. Menyimpan ke memory.json
        # ------
        if extracted_text:
            try: 
                vector_db.save_memory("File Info: " + extracted_text)
            except Exception: 
                pass
            
        if user_message:
            try: 
                vector_db.save_memory("User says: " + user_message)
            except Exception: 
                pass

        # ------
        # 4. Retrieve, mencari ingatan
        # ------
        relevant_memory = ""
        if user_message and user_message.strip() != "":
            relevant_memory = vector_db.search_memory(user_message)
            
        if extracted_text:
            relevant_memory += "\n\n[SYSTEM NOTE]: " + extracted_text

        # ------
        # 5. Prompt lengkap
        # ------
        prompt = "You are an Expert AI Finance Assistant. You are a Multimodal AI and CAN SEE IMAGES and PDFs perfectly.\n\n"
        prompt += "[1] USER'S ACTUAL FINANCIAL DATA (Database Dashboard):\n"
        prompt += json.dumps(financial_data) + "\n\n"
        prompt += "[2] RELEVANT PAST MEMORIES & SYSTEM NOTES:\n"
        prompt += relevant_memory + "\n\n"
        prompt += "[3] USER'S CURRENT MESSAGE:\n"
        prompt += user_message + "\n\n"
        prompt += "CRITICAL INSTRUCTIONS:\n"
        prompt += "- YOU HAVE VISION. NEVER say 'I am a text AI' or 'I cannot read files'.\n"
        prompt += "- If the user uploads a file, analyze it carefully and answer their question based on the visual.\n"
        prompt += "- If it is a receipt, acknowledge that the data was added to the database and calculate their new balance based on [1].\n"
        prompt += "- Provide a professional, accurate response in English."
        
        contents_to_send.append(prompt)
        
        # ------
        # 6. Hasilkan jawaban
        # ------
        response = model.generate_content(
            contents_to_send, 
            safety_settings=SAFETY_SETTINGS
        )
        
        final_answer = ""
        try:
            final_answer = response.text
        except ValueError:
            if response.prompt_feedback:
                final_answer = "System Error: Blocked by Google Safety filters. Detail: " + str(response.prompt_feedback)
            else:
                final_answer = "System Error: Failed to parse Google API text."
                
        return jsonify({"response": final_answer})
        
    except Exception as e:
        error_name = type(e).__name__
        return jsonify({"response": "**System Error:** [" + error_name + "] " + str(e)})
    
# ------
# 5. Jalankan Server
# ------
if __name__ == '__main__':
    app.run(debug=True)