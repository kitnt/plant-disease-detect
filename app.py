from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from ultralytics import YOLO
import os
import uuid
import base64
import json
import pymysql

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ========== 1. 加载分类模型 ==========
MODEL_PATH = os.path.join('model', 'best-cls.pt')
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH)
    CLASS_NAMES = model.names
    print(f"✅ 分类模型加载成功，类别数：{len(CLASS_NAMES)}")
else:
    model = None
    CLASS_NAMES = {}
    print(f"⚠️ 模型未找到：{MODEL_PATH}")

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ========== 2. 数据库 ==========
def get_db():
    return pymysql.connect(
        host='localhost', user='root', password='你的密码',
        database='leaf_disease', charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# ========== 3. HTTP 分类接口 ==========
@app.route('/api/classify', methods=['POST'])
def classify():
    if model is None:
        return jsonify({'code': 500, 'msg': '模型未加载'})

    file = request.files['image']
    uid = str(uuid.uuid4())
    ext = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'jpg'
    filename = f'{uid}.{ext}'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    results = model(filepath)
    probs = results[0].probs.data.tolist()
    top1_id = results[0].probs.top1
    top1_name = CLASS_NAMES[top1_id]
    top1_conf = probs[top1_id]
    prob_dict = {CLASS_NAMES[i]: round(p, 4) for i, p in enumerate(probs)}

    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO detection_record(original_image, disease_name, confidence, probabilities) VALUES(%s,%s,%s,%s)",
                (filename, top1_name, top1_conf, json.dumps(prob_dict, ensure_ascii=False))
            )
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ 数据库写入失败: {e}")

    return jsonify({
        'code': 200,
        'image': f'/static/uploads/{filename}',
        'disease': top1_name,
        'confidence': top1_conf,
        'probabilities': prob_dict
    })

# ========== 4. SocketIO ==========
@socketio.on('connect')
def test_connect():
    print('有客户端连接进来了！')
    emit('server_response', {'data': '连接成功！'})

@socketio.on('video_frame')
def handle_frame(data):
    if model is None:
        emit('classify_result', {'error': '模型未加载'})
        return
    try:
        img_b64 = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        uid = str(uuid.uuid4())
        filename = f'{uid}.jpg'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(img_b64))

        results = model(filepath)
        probs = results[0].probs.data.tolist()
        top1_id = results[0].probs.top1
        top1_name = CLASS_NAMES[top1_id]
        top1_conf = probs[top1_id]
        prob_dict = {CLASS_NAMES[i]: round(p, 4) for i, p in enumerate(probs)}

        emit('classify_result', {
            'disease': top1_name,
            'confidence': top1_conf,
            'probabilities': prob_dict
        })
    except Exception as e:
        emit('classify_result', {'error': str(e)})

# ========== 5. 病害信息 ==========
@app.route('/api/disease/<name>', methods=['GET'])
def disease_info(name):
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM disease_info WHERE name=%s", (name,))
            info = cur.fetchone()
        conn.close()
        return jsonify({'code': 200, 'data': info})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

# ========== 6. 首页 ==========
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
