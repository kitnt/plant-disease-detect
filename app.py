import os
import uuid
import json
import base64
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from ultralytics import YOLO
import pymysql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ========== 1. 加载分类模型 ==========
# 注意：模型文件不传 GitHub，运行时放到 model/best-cls.pt
MODEL_PATH = os.path.join('model', 'best-cls.pt')
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH)
    CLASS_NAMES = model.names
else:
    model = None
    print("⚠️ 模型未找到，请将 best-cls.pt 放入 model/ 目录")

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ========== 2. 数据库 ==========
def get_db():
    return pymysql.connect(
        host='localhost', user='root', password='你的密码',
        database='leaf_disease', charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# ========== 3. HTTP 分类接口（供 Vue 调用） ==========
@app.route('/api/classify', methods=['POST'])
def classify():
    if model is None:
        return jsonify({'code': 500, 'msg': '模型未加载'})

    file = request.files['image']
    uid = str(uuid.uuid4())
    ext = file.filename.rsplit('.', 1)[-1]
    filename = f'{uid}.{ext}'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # 分类推理
    results = model(filepath)
    probs = results[0].probs.data.tolist()
    top1_id = results[0].probs.top1
    top1_name = CLASS_NAMES[top1_id]
    top1_conf = probs[top1_id]

    prob_dict = {CLASS_NAMES[i]: round(p, 4) for i, p in enumerate(probs)}

    # 保存记录
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
        print(f"数据库写入失败: {e}")

    return jsonify({
        'code': 200,
        'image': f'/static/uploads/{filename}',
        'disease': top1_name,
        'confidence': top1_conf,
        'probabilities': prob_dict
    })

# ========== 4. SocketIO 实时通信（如果前端用 WebSocket） ==========
@socketio.on('image')
def handle_image(data):
    """前端通过 socket 发 base64 图片"""
    if model is None:
        emit('result', {'error': '模型未加载'})
        return

    # 解码 base64
    img_data = data['image'].split(',')[1]
    uid = str(uuid.uuid4())
    filename = f'{uid}.jpg'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(img_data))

    # 推理
    results = model(filepath)
    probs = results[0].probs.data.tolist()
    top1_id = results[0].probs.top1

    emit('result', {
        'disease': CLASS_NAMES[top1_id],
        'confidence': probs[top1_id],
        'probabilities': {CLASS_NAMES[i]: round(p, 4) for i, p in enumerate(probs)}
    })

# ========== 5. 页面路由 ==========
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
