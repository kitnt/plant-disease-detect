from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    print('有客户端连接进来了！')
    emit('server_response', {'data': '连接成功！'})

@socketio.on('video_frame')
def handle_frame(data):
    print('收到了前端发来的数据！')
    emit('detection_result', {'image': data, 'detections': []})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)