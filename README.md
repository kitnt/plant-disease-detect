# 植物病害检测
基于YOLOv8 + Flask + SocketIO的植物叶片病害实时识别平台

## 项目结构
- model/     YOLO模型相关代码（detect.py、train.py、data.yaml）
- templates/ 网页前端页面（index.html）
- static/    js、css静态资源
- docs/      项目文档、报告
- app.py     Flask后端服务
- requirements.txt 项目依赖包列表

## 环境安装
```bash
pip install -r requirements.txt
