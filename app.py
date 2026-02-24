from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import os
import random
import time
from datetime import datetime

app = Flask(__name__)
CORS(app) # อนุญาตให้หน้าเว็บคุยกับ Server ได้

# --- ตั้งค่าโฟลเดอร์เก็บรูปและฐานข้อมูล ---
# ใช้ os.getcwd() เพื่อหาโฟลเดอร์ปัจจุบันที่รันไฟล์ ป้องกันปัญหาหาไม่เจอ
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_FILE = os.path.join(BASE_DIR, 'data.json')

# สร้างโฟลเดอร์ uploads ถ้ายังไม่มี
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

# --- ฟังก์ชันจัดการฐานข้อมูล ---
def load_data():
    # ถ้าไม่มีไฟล์ หรือไฟล์ว่างเปล่า ให้สร้างใหม่
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return create_default_db()
    
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # ตรวจสอบว่ามีหัวข้อครบไหม ถ้าขาดให้เติม
            keys_needed = ['users', 'repairs', 'installs', 'messages']
            changed = False
            for k in keys_needed:
                if k not in data:
                    data[k] = []
                    changed = True
            
            # ถ้ามี User แต่ไม่มี admin ให้เติม (กันเหนียว)
            if not data['users']:
                return create_default_db()
                
            if changed: save_data(data)
            return data
    except:
        return create_default_db()

def create_default_db():
    default_data = {
        'users': [
            {'u': 'admin', 'p': '1234', 'name': 'พี่เก้ง (Manager)', 'role': 'MANAGER', 'tel': '081-234-5678', 'avatar': ''},
            {'u': 'tech1', 'p': '1111', 'name': 'ช่างบิว', 'role': 'TECH', 'tel': '090-999-8888', 'avatar': ''}
        ],
        'repairs': [],
        'installs': [],
        'messages': []
    }
    save_data(default_data)
    return default_data

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- API: หน้าแรก ---
@app.route('/')
def home():
    return "<h1>✅ MMTS System API is Running (Full Version)</h1>"

# --- API: ระบบล็อกอิน (Login) ---
@app.route('/api/login', methods=['POST'])
def login():
    data = load_data()
    req = request.json
    username = req.get('username', '').strip().lower()
    password = req.get('password', '').strip()

    print(f"Login attempt: {username} | {password}") # Debug ดูในจอดำ

    # ค้นหา user
    found = None
    for u in data['users']:
        if u['u'].lower() == username and u['p'] == password:
            found = u
            break
    
    if found:
        return jsonify({'status': 'success', 'user': found}), 200
    else:
        return jsonify({'status': 'fail', 'message': 'ชื่อผู้ใช้หรือรหัสผ่านผิด'}), 401

# --- API: จัดการผู้ใช้งาน (Users) ---
@app.route('/api/users', methods=['GET', 'POST'])
def manage_users():
    data = load_data()
    if request.method == 'GET':
        return jsonify(data['users'])
    
    # เพิ่มผู้ใช้ใหม่
    if request.method == 'POST':
        new_user = request.json
        # เช็กชื่อซ้ำ
        for u in data['users']:
            if u['u'] == new_user['u']:
                return jsonify({'status': 'error', 'message': 'ชื่อผู้ใช้นี้มีอยู่แล้ว'}), 400
        
        data['users'].append(new_user)
        save_data(data)
        return jsonify({'status': 'success'})

@app.route('/api/users/<uid>', methods=['PUT', 'DELETE'])
def action_user(uid):
    data = load_data()
    if request.method == 'DELETE':
        # ห้ามลบ admin
        if uid == 'admin': return jsonify({'status': 'error', 'message': 'ห้ามลบ Admin'}), 400
        data['users'] = [u for u in data['users'] if u['u'] != uid]
        save_data(data)
        return jsonify({'status': 'success'})
    
    if request.method == 'PUT':
        for u in data['users']:
            if u['u'] == uid:
                u.update(request.json) # อัปเดตข้อมูล
                save_data(data)
                return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

# --- API: งานแจ้งซ่อม (Repairs) ---
@app.route('/api/repairs', methods=['GET', 'POST'])
def manage_repairs():
    data = load_data()
    if request.method == 'GET':
        return jsonify(data['repairs'])
    
    if request.method == 'POST':
        job = request.json
        job['id'] = f"TK-{random.randint(10000, 99999)}" # สร้าง ID สุ่ม
        if 'status' not in job: job['status'] = 'PENDING'
        data['repairs'].append(job)
        save_data(data)
        return jsonify({'status': 'success'})

@app.route('/api/repairs/<jid>', methods=['PUT', 'DELETE'])
def action_repair(jid):
    data = load_data()
    if request.method == 'DELETE':
        data['repairs'] = [j for j in data['repairs'] if j['id'] != jid]
    
    if request.method == 'PUT':
        for j in data['repairs']:
            if j['id'] == jid:
                j.update(request.json)
    
    save_data(data)
    return jsonify({'status': 'success'})

# --- API: งานติดตั้ง (Installs) ---
@app.route('/api/installs', methods=['GET', 'POST'])
def manage_installs():
    data = load_data()
    if request.method == 'GET':
        return jsonify(data['installs'])
    
    if request.method == 'POST':
        job = request.json
        job['id'] = f"IN-{random.randint(10000, 99999)}"
        if 'status' not in job: job['status'] = 'PENDING'
        data['installs'].append(job)
        save_data(data)
        return jsonify({'status': 'success'})

@app.route('/api/installs/<jid>', methods=['PUT', 'DELETE'])
def action_install(jid):
    data = load_data()
    if request.method == 'DELETE':
        data['installs'] = [j for j in data['installs'] if j['id'] != jid]
    
    if request.method == 'PUT':
        for j in data['installs']:
            if j['id'] == jid:
                j.update(request.json)
    
    save_data(data)
    return jsonify({'status': 'success'})

# --- API: ระบบแชท (Chat) ---
@app.route('/api/messages', methods=['GET', 'POST'])
def manage_chat():
    data = load_data()
    if request.method == 'GET':
        return jsonify(data.get('messages', []))
    
    if request.method == 'POST':
        msg = request.json
        msg['time'] = datetime.now().strftime("%H:%M")
        data['messages'].append(msg)
        # เก็บไว้แค่ 100 ข้อความล่าสุดก็พอ (กันไฟล์บวม)
        if len(data['messages']) > 100:
            data['messages'] = data['messages'][-100:]
        save_data(data)
        return jsonify({'status': 'success'})

# --- API: อัปโหลดไฟล์ (Images/Videos) ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # ตั้งชื่อไฟล์ใหม่ด้วยเวลา (Timestamp) เพื่อไม่ให้ชื่อซ้ำกัน
        timestamp = int(time.time())
        original_name = secure_filename(file.filename)
        new_filename = f"{timestamp}_{original_name}"
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        return jsonify({'filename': new_filename}), 200

# --- API: เรียกดูรูปภาพ ---
@app.route('/uploads/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # โหลดข้อมูลครั้งแรก
    load_data()
    print("---------------------------------------------------")
    print("🚀 MMTS SERVER STARTED (Full Features)")
    print("📂 Database File:", DB_FILE)
    print("📂 Upload Folder:", UPLOAD_FOLDER)
    print("---------------------------------------------------")
    app.run(debug=True, port=5000)