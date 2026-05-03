# TINYPROJECT
This repositry is for the tiny project we are making this smemester
🎭 EmotiCam — Real-Time Emotion & Gesture Chat
A lightweight real-time video chat application that detects facial emotions and hand gestures using computer vision — without heavy AI models like DeepFace or FER.

🚀 Features


🔐 User Authentication (Login / Signup)


🏠 Create & Join Chat Rooms


💬 Real-time Chat (WebSockets)


🎥 Live Video Processing (low bandwidth)


😀 Face Emotion Detection (rule-based)


✋ Hand Gesture Recognition (MediaPipe)


⚡ Fast & Lightweight (no deep learning models)


🎨 Client-side overlays (no video flicker)



🧠 How It Works
📡 Architecture
Browser → sends video frames (base64)        → Server processes frames (OpenCV + MediaPipe)        → Server sends JSON (faces + gestures)        → Browser draws overlays on canvas
⚡ Key Idea


Only metadata is sent back (not video)


Reduces bandwidth and improves speed


No laggy or flickering video



🧩 Tech Stack
Backend


Python


Flask


Flask-SocketIO


Computer Vision


OpenCV (face detection)


MediaPipe (hand tracking)


Frontend


HTML / CSS / JavaScript


Canvas API (overlay rendering)



📂 Project Structure
├── app.py                # Main server (routes + sockets)├── emotion_engine.py     # Emotion & gesture detection logic├── requirements.txt      # Python dependencies├── users.json            # Local user database├── templates/            # HTML pages (login, lobby, room)├── .gitignore            # Ignored files

😀 Emotion Detection (Rule-Based)
No AI model is used. Emotions are detected using simple logic:


Smile detected → 😄 Happy


No eyes detected → 😴 Sleepy


Large face → 🤩 Excited


Otherwise → 😐 Neutral


✔ Very fast
✔ No GPU required

✋ Hand Gesture Detection
Uses MediaPipe Hands to detect gestures:


👍 Thumbs Up


✌️ Peace


👋 Wave


🤙 Call Me


🤟 Love Sign


🖐 Open Hand


✊ Fist


☝️ Pointing



⚙️ Installation
1. Clone the repository
git clone https://github.com/your-username/emoticam.gitcd emoticam
2. Install dependencies
pip install -r requirements.txt
3. Run the server
python app.py
4. Open in browser
http://localhost:5000

📦 Requirements
From requirements.txt:


flask


flask-socketio


eventlet


opencv-python


numpy


pillow


mediapipe



🔐 Authentication


Passwords are hashed using SHA-256


Stored locally in users.json



📡 API Endpoints
EndpointDescription/loginUser login/signupRegister user/lobbyLobby page/room/<code>Join room/api/create_roomCreate room/api/join_roomJoin room

🔌 Socket Events


video_frame → send video frame


detection_result → receive emotion + gesture data


chat_message → chat system


user_joined / user_left → room updates



⚡ Performance Optimizations


Frames resized before processing


Detection runs in background thread


Only JSON returned (no images)


Reduced bandwidth usage (~10× improvement)



🔒 Git Ignore
This project includes a .gitignore file to keep the repository clean and secure.
Ignored Files:
venv/__pycache__/*.pyc.env
Why?


Avoid uploading unnecessary files


Protect sensitive data


Keep repository lightweight



🔥 Key Highlight

This project performs real-time emotion detection WITHOUT DeepFace, FER, or heavy AI models


📌 Future Improvements


Add AI-based emotion detection


Voice emotion analysis 🎤


Better gesture accuracy


UI improvements


Cloud deployment



👨‍💻 Author
Kanishka Goyal
Shrishti Tiwari
Aryan Tiwari
Kavya Lamba

📜 License
This project is open-source and free to use.

If you want next level, I can:


Add GitHub badges + screenshots + demo GIF (makes your repo look 🔥)


Or convert this into a perfect viva/project submission document


Just tell me 👍
