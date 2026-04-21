from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import cv2
import numpy as np
import base64
import json
import os
import hashlib
import secrets
import string
import logging
from datetime import datetime
from emotion_engine import EmotionEngine

# ───────────── Logging ─────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("emoticam")

app = Flask(__name__)
app.secret_key = os.environ.get("EMOTICAM_SECRET", "emoticam_secret_key_2024")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    max_http_buffer_size=5 * 1024 * 1024,   # 5 MB cap (down from 10)
    ping_timeout=20,
    ping_interval=10,
)

emotion_engine = EmotionEngine()

# ───────────── Users ──────────────────────────────────────────
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ───────────── Rooms ──────────────────────────────────────────
active_rooms: dict[str, dict] = {}
# Map socket_id → room_code for fast lookups (no looping)
sid_to_room: dict[str, str] = {}

def generate_room_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(6))
        if code not in active_rooms:
            return code

# ───────────── Routes ─────────────────────────────────────────
@app.route("/")
def index():
    return redirect("/lobby" if "username" in session else "/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"]
        users = load_users()
        if u in users and users[u]["password"] == hash_password(p):
            session["username"] = u
            session["avatar"] = users[u].get("avatar", "😊")
            return redirect("/lobby")
        error = "Invalid credentials"
    return render_template("login.html", error=error)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"]
        c = request.form["confirm"]
        a = request.form.get("avatar", "😊")
        users = load_users()
        if len(u) < 3:
            error = "Username too short"
        elif u in users:
            error = "User already exists"
        elif len(p) < 6:
            error = "Password too short (min 6 chars)"
        elif p != c:
            error = "Passwords do not match"
        else:
            users[u] = {"password": hash_password(p), "avatar": a}
            save_users(users)
            session["username"] = u
            session["avatar"] = a
            return redirect("/lobby")
    return render_template("signup.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/lobby")
def lobby():
    if "username" not in session:
        return redirect("/login")
    return render_template("lobby.html",
                           username=session["username"],
                           avatar=session.get("avatar", "😊"))


@app.route("/room/<code>")
def room(code):
    if "username" not in session:
        return redirect("/login")
    if code not in active_rooms:
        return redirect("/lobby")
    return render_template("room.html",
                           username=session["username"],
                           avatar=session.get("avatar", "😊"),
                           room_code=code,
                           room_info=active_rooms[code])

# ───────────── API ─────────────────────────────────────────────
@app.route("/api/create_room", methods=["POST"])
def create_room():
    if "username" not in session:
        return jsonify({"error": "not logged in"}), 401
    code = generate_room_code()
    active_rooms[code] = {
        "host": session["username"],
        "members": [session["username"]],
        "created_at": datetime.now().strftime("%H:%M"),
    }
    log.info(f"Room {code} created by {session['username']}")
    return jsonify({"code": code})


@app.route("/api/join_room", methods=["POST"])
def join_room_api():
    if "username" not in session:
        return jsonify({"error": "not logged in"}), 401
    code = (request.json or {}).get("code", "").upper().strip()
    if code not in active_rooms:
        return jsonify({"error": "Room not found"}), 404
    return jsonify({"code": code})

# ───────────── Sockets ────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    log.info(f"Socket connected: {request.sid}")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    code = sid_to_room.pop(sid, None)
    if code and code in active_rooms:
        username = session.get("username", "?")
        active_rooms[code]["members"] = [
            m for m in active_rooms[code]["members"] if m != username
        ]
        if not active_rooms[code]["members"]:
            del active_rooms[code]
            log.info(f"Room {code} deleted (empty)")
        else:
            emit("user_left", {
                "username": username,
                "members": active_rooms[code]["members"],
            }, to=code)


@socketio.on("join_room_socket")
def join_room_socket(data):
    code = (data or {}).get("code", "")
    username = session.get("username")
    if not code or code not in active_rooms or not username:
        return
    join_room(code)
    sid_to_room[request.sid] = code          # O(1) lookup — no loop needed
    if username not in active_rooms[code]["members"]:
        active_rooms[code]["members"].append(username)
    emit("user_joined", {
        "username": username,
        "members": active_rooms[code]["members"],
    }, to=code)


@socketio.on("leave_room_socket")
def leave_room_socket(data):
    code = (data or {}).get("code", "")
    username = session.get("username")
    sid_to_room.pop(request.sid, None)
    if code and code in active_rooms:
        active_rooms[code]["members"] = [
            m for m in active_rooms[code]["members"] if m != username
        ]
        leave_room(code)
        emit("user_left", {
            "username": username,
            "members": active_rooms[code].get("members", []),
        }, to=code)


@socketio.on("chat_message")
def chat(data):
    code = (data or {}).get("room")
    if not code:
        return
    emit("chat_message", {
        "username": session.get("username"),
        "avatar": session.get("avatar", "😊"),
        "message": (data.get("message") or "")[:500],   # cap message length
        "time": datetime.now().strftime("%H:%M"),
    }, to=code)


# ───────────── 🔥 VIDEO — metadata-only, zero frame roundtrip ──
# Architecture:
#   Browser → sends 320×240 JPEG (10 fps) → server detects emotion/gesture
#   Server  → sends back ONLY lightweight JSON (face boxes + emotions + gestures)
#   Browser → draws overlays on <canvas> that sits on top of <video>
#   Result  → NO flicker, NO base64 roundtrip, ~10× less bandwidth
# ──────────────────────────────────────────────────────────────

@socketio.on("video_frame")
def video_frame(data):
    try:
        username = session.get("username")
        if not username:
            return

        # Fast O(1) room lookup using sid map
        code = sid_to_room.get(request.sid)
        if not code:
            return

        # Decode incoming frame
        raw = (data.get("image") or "")
        if "," in raw:
            raw = raw.split(",", 1)[1]
        img_bytes = base64.b64decode(raw)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return

        # emotion_engine.process_meta returns (faces, hands) — NO frame drawing
        # This is our optimized path; falls back to legacy process() if needed
        if hasattr(emotion_engine, "process_meta"):
            faces, hands = emotion_engine.process_meta(frame)
        else:
            # Legacy: still works, just ignore the annotated frame
            _, faces, hands = emotion_engine.process(frame)

        # Emit lightweight JSON only — no image data sent back
        print("FACES DATA:", faces)
        emit("detection_result", {
            "username": username,
            "faces": faces,
            "hands": hands,
        }, to=code)

    except Exception as e:
        log.warning(f"video_frame error: {e}")


# ───────────── Run ─────────────────────────────────────────────
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
