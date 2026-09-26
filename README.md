# 植物叶片病害分类平台

基于 YOLOv8 分类模型 + Flask + SocketIO 的植物叶片病害实时识别平台。

## 项目简介

用户上传植物叶片图片，后端使用 YOLOv8 分类模型进行推理，返回病害类别和置信度，并支持保存识别记录。

## 技术栈

- **模型**：YOLOv8 分类模型（YOLOv8s-cls）
- **后端**：Flask + Flask-SocketIO
- **前端**：HTML + CSS + JavaScript + Socket.IO
- **数据库**：MySQL（待接入）
- **深度学习框架**：Ultralytics + PyTorch

## 项目结构
plant-disease-classify/
├── model/              # YOLO 模型相关代码
│   ├── train.py        # 训练脚本
│   ├── detect.py       # 单图推理脚本
│   └── best.pt         # 训练好的分类权重（不上传GitHub）
├── templates/          # 前端 HTML 页面
│   └── index.html      # 上传图片、显示识别结果
├── static/             # 静态资源
│   ├── css/
│   └── js/
├── docs/               # 项目文档、报告
├── app.py              # Flask 后端服务主文件
├── requirements.txt    # Python 依赖包列表
└── README.md           # 项目说明文档
## 核心功能

- ✅ 图片上传识别：用户选择本地叶片图片，上传后由 YOLOv8 分类模型推理
- ✅ 实时返回结果：通过 Socket.IO 将识别结果（病害类别 + 置信度）实时显示在页面
- 🔄 识别记录持久化：MySQL 保存历史识别记录（开发中）
- 🔄 病害信息展示：识别后弹出病害症状与防治建议（开发中）

## 环境安装

```bash
pip install -r requirements.txt
```

启动项目

```bash
python app.py
```

浏览器访问：http://127.0.0.1:5000

开发规范

1. 不要直接推 main 分支，必须建分支提 PR。
2. .pt 模型权重文件、数据集不要上传 GitHub（已在 .gitignore 中忽略）。
3. Socket.IO 事件名统一：
   · 前端 → 后端：video_frame（发送图片 Base64）
   · 后端 → 前端：detection_result（返回识别结果）

小组分工

角色 负责内容
模型组 数据集准备、YOLOv8 分类模型训练、交付 best.pt
后端组 Flask + SocketIO + YOLO 推理集成 + 数据库
前端组 页面上传、结果展示、UI 美化
接口格式

前端发送（video_frame）：

```json
"data:image/jpeg;base64,/9j/4AAQSk..."
```

后端返回（detection_result）：

```json
{
  "class_name": "early_blight",
  "confidence": 0.92
}
```
改完之后怎么推送

在终端里依次敲：
```bash
git add README.md
git commit -m "docs: 更新README为分类版项目说明"
git push origin main
```
