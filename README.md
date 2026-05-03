

# 🎭 EmotiCam

### Real-Time Emotion & Gesture Chat using Computer Vision

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 📌 Overview

**EmotiCam** is a real-time video chat application that detects **facial emotions** and **hand gestures** using lightweight computer vision techniques.

Unlike typical systems, it **does NOT use heavy AI models** (like DeepFace or FER), making it:

* ⚡ Fast
* 💻 Lightweight
* 🚀 Easy to run on any system

---

## ✨ Features

* 🔐 Authentication (Login / Signup)
* 🏠 Create & Join Rooms
* 💬 Real-time Chat (Socket.IO)
* 🎥 Live Video Processing
* 😀 Emotion Detection (Rule-based)
* ✋ Hand Gesture Recognition (MediaPipe)
* 🎨 Smooth overlay rendering (no flicker)

---

## 🧠 How It Works

```
Client (Browser)
   ↓ sends frames
Server (Flask + OpenCV + MediaPipe)
   ↓ processes
Server returns JSON (faces + gestures)
   ↓
Client draws overlays on canvas
```

### ⚡ Why it's fast

* No video returned from server
* Only metadata (JSON) is sent
* Background processing thread

---

## 🛠 Tech Stack

**Backend**

* Python
* Flask
* Flask-SocketIO

**Computer Vision**

* OpenCV (face detection)
* MediaPipe (hand tracking)

**Frontend**

* HTML / CSS / JavaScript
* Canvas API

---

## 📂 Project Structure

```
.
├── app.py
├── emotion_engine.py
├── requirements.txt
├── users.json
├── templates/
└── .gitignore
```

---

## 😀 Emotion Detection Logic

This project uses **rule-based detection** instead of deep learning:

| Condition        | Emotion    |
| ---------------- | ---------- |
| Smile detected   | 😄 Happy   |
| No eyes detected | 😴 Sleepy  |
| Large face       | 🤩 Excited |
| Default          | 😐 Neutral |

---

## ✋ Supported Hand Gestures

* 👍 Thumbs Up
* ✌️ Peace
* 👋 Wave
* 🤙 Call Me
* 🤟 Love Sign
* 🖐 Open Hand
* ✊ Fist
* ☝️ Pointing

---

## ⚙️ Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/emoticam.git
cd emoticam
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python app.py
```

### 4. Open in browser

```
http://localhost:5000
```

---

## 📦 Dependencies

```
flask
flask-socketio
eventlet
opencv-python
numpy
pillow
mediapipe
```

---

## 🔐 Security

* Passwords hashed using SHA-256
* `.env` ignored via `.gitignore`

---

## 🔒 .gitignore

```
venv/
__pycache__/
*.pyc
.env
```

---

## ⚡ Performance Highlights

* 🔄 Background processing thread
* 📉 Reduced frame size before detection
* 📡 JSON-only communication
* 🚀 ~10x lower bandwidth usage

---

## 🚧 Future Improvements

* AI-based emotion detection
* Voice emotion analysis
* UI enhancements
* Cloud deployment

---

## 👤 Author

**Kannu**

---

## 📜 License

This project is open-source and free to use.

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!

---

### 🔥 What makes THIS version GitHub-perfect:

* Badges ✅
* Clean sections ✅
* Tables ✅
* Code blocks without IDs (important) ✅
* Scannable layout ✅
* Professional tone ✅

