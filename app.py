from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai
import db_manager
import json
import os
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
# Rute Savings Goal
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
# 3. Rute Chatbot
# ------
@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    user_message = request.form.get("message", "")
    uploaded_file = request.files.get("file")
    
    financial_data = db_manager.get_all_transactions()
    
    prompt = f"""
    You are an AI Finance Planner. 
    User's current database: {json.dumps(financial_data)}.
    Respond to the user's message appropriately.
    User message: {user_message}
    """
    
    contents_to_send = [prompt]
    file_path = None
    
    try:
        if uploaded_file and uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(file_path)
            
            ai_file = genai.upload_file(path=file_path)
            contents_to_send.append(ai_file)
            prompt += "\nI have attached a file/image. Please analyze it."
            
        response = model.generate_content(contents_to_send)
        ai_reply = response.text
        
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        return jsonify({"response": ai_reply})
        
    except Exception as e:
        return jsonify({"response": f"Error interacting with AI: {str(e)}"})

# ------
# Jalankan Server
# ------
if __name__ == '__main__':
    app.run(debug=True)