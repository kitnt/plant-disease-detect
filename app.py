from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from ultralytics import YOLO
import base64
import cv2
import numpy as np

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# 注意：分类模型的权重名通常是 yolov8s-cls.pt，训练出来的叫 best.pt
# 假设算法组已经训练好了，放在 model/best.pt 里
model = YOLO('yolov8n-cls.pt')  

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    print('客户端已连接')
    emit('server_response', {'data': '连接成功！'})

@socketio.on('video_frame')
def handle_frame(data):
    print('收到前端发来的图像帧')
    
    # 1. 把前端发来的 base64 字符串解码成图片
    img_data = base64.b64decode(data.split(',')[1])
    nparr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 2. 用分类模型推理
    results = model(frame)
    probs = results[0].probs  # 分类模型输出的是概率
    top1_idx = probs.top1
    top1_conf = float(probs.top1conf)
    class_name = results[0].names[top1_idx]

    # 3. 把结果发回前端
    emit('detection_result', {
        'class_name': class_name,
        'confidence': round(top1_conf, 3)
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
