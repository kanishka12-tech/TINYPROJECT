# ── eventlet must be first ────────────────────────────────────
# import eventlet
# eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import json, os, hashlib, secrets, string, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("emoticam")

app = Flask(__name__)
app.secret_key = os.environ.get("EMOTICAM_SECRET", "emoticam_secret_key_2024")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
)

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
sid_to_room: dict[str, str]   = {}

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
        if   len(u) < 3:    error = "Username too short"
        elif u in users:    error = "User already exists"
        elif len(p) < 6:    error = "Password too short (min 6 chars)"
        elif p != c:        error = "Passwords do not match"
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
        "peers": {},
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

# ═══════════════════════════════════════════════════════════════
# SOCKET.IO  — SIGNALING ONLY
# ═══════════════════════════════════════════════════════════════
@socketio.on("connect")
def on_connect():
    log.info(f"Socket connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    code = sid_to_room.pop(sid, None)
    if not code or code not in active_rooms:
        return
    room_data = active_rooms[code]
    username  = room_data["peers"].pop(sid, None)

    if username:
        still_connected = username in room_data["peers"].values()
        if not still_connected:
            room_data["members"] = [m for m in room_data["members"] if m != username]

    if not room_data["members"]:
        del active_rooms[code]
        log.info(f"Room {code} deleted (empty)")
    else:
        emit("user_left", {
            "sid": sid,
            "username": username or "?",
            "members": room_data["members"],
        }, to=code)

@socketio.on("join_room_socket")
def on_join_room(data):
    code = (data or {}).get("code", "")
    username = session.get("username")
    if not code or not username:
        return
    if code not in active_rooms:
        emit("room_closed", {"code": code})
        return
    join_room(code)
    sid_to_room[request.sid] = code
    if username not in active_rooms[code]["members"]:
        active_rooms[code]["members"].append(username)

    emit("user_joined", {
        "sid": request.sid,
        "username": username,
        "members": active_rooms[code]["members"],
    }, to=code)

@socketio.on("ready_for_peers")
def on_ready_for_peers(data):
    code = (data or {}).get("code", "")
    username = session.get("username")

    if not code or code not in active_rooms or not username:
        return

    room_data = active_rooms[code]

    # Send existing peers FIRST
    existing = [
        {"sid": sid, "username": uname}
        for sid, uname in room_data["peers"].items()
    ]

    emit("existing_peers", {"peers": existing})

    # THEN add current user
    room_data["peers"][request.sid] = username

@socketio.on("signal")
def on_signal(data):
    target_sid = (data or {}).get("to")
    signal     = (data or {}).get("signal")
    if not target_sid or signal is None:
        return
    emit("signal", {
        "from": request.sid,
        "fromUsername": session.get("username", "?"),
        "signal": signal,
    }, to=target_sid)

@socketio.on("leave_room_socket")
def on_leave_room(data):
    code = (data or {}).get("code", "")
    username = session.get("username")
    sid_to_room.pop(request.sid, None)
    if code and code in active_rooms:
        room_data = active_rooms[code]
        room_data["peers"].pop(request.sid, None)
        if username:
            still_connected = username in room_data["peers"].values()
            if not still_connected:
                room_data["members"] = [m for m in room_data["members"] if m != username]
        leave_room(code)
        emit("user_left", {
            "sid": request.sid,
            "username": username or "?",
            "members": room_data.get("members", []),
        }, to=code)

@socketio.on("chat_message")
def on_chat(data):
    code = (data or {}).get("room")
    if not code:
        return
    emit("chat_message", {
        "username": session.get("username"),
        "avatar": session.get("avatar", "😊"),
        "message": (data.get("message") or "")[:500],
        "time": datetime.now().strftime("%H:%M"),
    }, to=code)

# ───────────── Run ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
