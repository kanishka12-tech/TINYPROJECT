print("🔥 emotion_engine.py LOADED")

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import threading

# ─── Emotions ───────────────────────────────────────────────────────────────
EMOTIONS = {
    'happy':       {'emoji': '😄', 'color': (34, 197, 94)},
    'sad':         {'emoji': '😢', 'color': (96, 165, 250)},
    'angry':       {'emoji': '😡', 'color': (239, 68, 68)},
    'fear':        {'emoji': '😨', 'color': (167, 139, 250)},
    'surprise':    {'emoji': '😲', 'color': (251, 191, 36)},
    'disgust':     {'emoji': '🤢', 'color': (74, 222, 128)},
    'neutral':     {'emoji': '😐', 'color': (148, 163, 184)},
    'excited':     {'emoji': '🤩', 'color': (249, 115, 22)},
    'love':        {'emoji': '😍', 'color': (244, 63, 94)},
    'joyful':      {'emoji': '🥳', 'color': (52, 211, 153)},
    'content':     {'emoji': '🙂', 'color': (110, 231, 183)},
    'proud':       {'emoji': '😤', 'color': (129, 140, 248)},
    'grateful':    {'emoji': '🙏', 'color': (163, 230, 53)},
    'hopeful':     {'emoji': '🌈', 'color': (56, 189, 248)},
    'playful':     {'emoji': '😜', 'color': (251, 146, 60)},
    'silly':       {'emoji': '🤪', 'color': (232, 121, 249)},
    'confused':    {'emoji': '🤔', 'color': (148, 163, 184)},
    'anxious':     {'emoji': '😰', 'color': (139, 92, 246)},
    'nervous':     {'emoji': '😬', 'color': (167, 139, 250)},
    'bored':       {'emoji': '😑', 'color': (100, 116, 139)},
    'tired':       {'emoji': '😪', 'color': (71, 85, 105)},
    'stressed':    {'emoji': '🤯', 'color': (220, 38, 38)},
    'frustrated':  {'emoji': '😤', 'color': (234, 88, 12)},
    'hurt':        {'emoji': '🥺', 'color': (147, 197, 253)},
    'lonely':      {'emoji': '🫂', 'color': (99, 102, 241)},
    'embarrassed': {'emoji': '😳', 'color': (251, 113, 133)},
    'shy':         {'emoji': '🫣', 'color': (244, 114, 182)},
    'smug':        {'emoji': '😎', 'color': (250, 204, 21)},
    'mischievous': {'emoji': '😈', 'color': (168, 85, 247)},
    'calm':        {'emoji': '😌', 'color': (94, 234, 212)},
    'sleepy':      {'emoji': '😪', 'color': (71, 85, 105)},
}

EXTENDED_MAP = {
    'happy':   [(0.85,'excited'),(0.70,'joyful'),(0.55,'love'),(0.40,'content'),(0.0,'happy')],
    'neutral': [(0.70,'calm'),(0.50,'bored'),(0.0,'neutral')],
    'angry':   [(0.80,'frustrated'),(0.60,'stressed'),(0.0,'angry')],
    'fear':    [(0.70,'anxious'),(0.50,'nervous'),(0.0,'fear')],
    'sad':     [(0.70,'hurt'),(0.50,'lonely'),(0.0,'sad')],
    'surprise':[(0.0,'surprise')],
    'disgust': [(0.0,'disgust')],
}

HAND_GESTURES = {
    'thumbs_up':   {'emoji': '👍', 'label': 'Thumbs Up',       'color': (34, 197, 94)},
    'thumbs_down': {'emoji': '👎', 'label': 'Thumbs Down',     'color': (239, 68, 68)},
    'peace':       {'emoji': '✌️', 'label': 'Peace',            'color': (56, 189, 248)},
    'ok':          {'emoji': '👌', 'label': 'OK',               'color': (52, 211, 153)},
    'fist':        {'emoji': '✊', 'label': 'Fist',             'color': (99, 102, 241)},
    'open_hand':   {'emoji': '🖐️', 'label': 'Open Hand',       'color': (251, 191, 36)},
    'pointing':    {'emoji': '☝️', 'label': 'Pointing',         'color': (249, 115, 22)},
    'rock':        {'emoji': '🤘', 'label': 'Rock On',          'color': (168, 85, 247)},
    'call_me':     {'emoji': '🤙', 'label': 'Call Me',          'color': (6, 182, 212)},
    'love_sign':   {'emoji': '🤟', 'label': 'Love Sign',        'color': (244, 63, 94)},
    'crossed':     {'emoji': '🤞', 'label': 'Fingers Crossed',  'color': (250, 204, 21)},
    'pinch':       {'emoji': '🤌', 'label': 'Pinch',            'color': (234, 88, 12)},
    'wave':        {'emoji': '👋', 'label': 'Wave',             'color': (74, 222, 128)},
    'pray':        {'emoji': '🙏', 'label': 'Pray / Thanks',    'color': (163, 230, 53)},
    'vulcan':      {'emoji': '🖖', 'label': 'Vulcan',           'color': (100, 116, 139)},
    'stop':        {'emoji': '🛑', 'label': 'Stop',             'color': (239, 68, 68)},
}

# ─── CSS hex colours for JSON output (used by JS canvas renderer) ────────────
def _rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

EMOTION_HEX = {k: _rgb_to_hex(v['color']) for k, v in EMOTIONS.items()}
HAND_HEX    = {k: _rgb_to_hex(v['color']) for k, v in HAND_GESTURES.items()}


def map_extended_emotion(base_emotion, score):
    for threshold, mapped in EXTENDED_MAP.get(base_emotion, [(0.0, base_emotion)]):
        if score >= threshold:
            return mapped
    return base_emotion


def get_font(size=60):
    for path in [
        "C:/Windows/Fonts/seguiemj.ttf",
        "C:/Windows/Fonts/seguisym.ttf",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def fingers_up(lm, is_right):
    f = [lm[4].x < lm[3].x if is_right else lm[4].x > lm[3].x]
    for tip in [8, 12, 16, 20]:
        f.append(lm[tip].y < lm[tip - 2].y)
    return f


def classify_hand(fingers, lm):
    t, i, m, r, p = fingers
    n = sum(fingers)
    if n == 0:
        return 'thumbs_down' if lm[4].y > lm[0].y else 'fist'
    if t and not i and not m and not r and not p:
        return 'thumbs_up'
    if n == 5:
        return 'open_hand'
    if not t and i and not m and not r and not p:
        return 'pointing'
    if not t and i and m and not r and not p:
        dist = ((lm[8].x-lm[12].x)**2+(lm[8].y-lm[12].y)**2)**0.5
        return 'crossed' if dist < 0.035 else 'peace'
    if not t and i and not m and not r and p:
        return 'rock'
    if t and not i and not m and not r and p:
        return 'call_me'
    if t and i and not m and not r and p:
        return 'love_sign'
    if not t and i and m and r and p:
        return 'vulcan' if abs(lm[12].x - lm[16].x) > 0.04 else 'stop'
    if m and r and p:
        if ((lm[4].x-lm[8].x)**2+(lm[4].y-lm[8].y)**2)**0.5 < 0.05:
            return 'ok'
    if not m and not r and not p:
        if ((lm[4].x-lm[8].x)**2+(lm[4].y-lm[8].y)**2)**0.5 < 0.04:
            return 'pinch'
    if t and n >= 4:
        return 'wave'
    if t and i and m and not r and not p:
        return 'pray'
    return 'open_hand'


class EmotionEngine:
    def __init__(self):
        # ── Haar cascades (no heavy models, no DeepFace) ──────────────────────
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_smile.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )

        # ── Threading / result cache ───────────────────────────────────────────
        self._pending   = None
        self._lock      = threading.Lock()
        self._res_lock  = threading.Lock()
        self._last_faces = []
        self._last_hands = []
        self._frame_n    = 0

        # ── MediaPipe hands ────────────────────────────────────────────────────
        self.mp_hands = None
        self.mp_draw  = None
        self.hands    = None
        self._load_hands()

        print("👉 Face detector: cv (Haar cascade, no DeepFace)")
        threading.Thread(target=self._bg_loop, daemon=True).start()

    # ── Model loading ──────────────────────────────────────────────────────────
    def _load_hands(self):
        try:
            import mediapipe as mp
            print("👉 MediaPipe imported successfully")

            self.mp_hands = mp.solutions.hands
            self.mp_draw  = mp.solutions.drawing_utils

            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            print("🔥 MediaPipe Hands initialised successfully")
        except Exception as e:
            print("❌ MediaPipe error:", e)
            self.hands = None

    # ── Background processing loop ─────────────────────────────────────────────
    def _bg_loop(self):
        """Daemon thread — picks up pending frames and runs detection."""
        while True:
            frame = None
            with self._lock:
                if self._pending is not None:
                    frame = self._pending.copy()
                    self._pending = None
            if frame is not None:
                faces = self._detect_faces(frame)
                hands = self._detect_hands(frame)
                with self._res_lock:
                    self._last_faces = faces
                    self._last_hands = hands
            else:
                threading.Event().wait(0.015)

    # ── Face detection (OpenCV Haar only) ─────────────────────────────────────
    def _detect_faces(self, frame):
        """
        Returns a list of dicts:
            {
                'box':     [x, y, w, h],
                'emotion': str,
                'base':    str,
                'score':   float,
                'all':     {emotion: score, ...},
            }

        Emotion rules (no AI model required):
            smile detected          → 'happy'
            no eyes detected        → 'sleepy'
            face area > 20 000 px²  → 'excited'   (face is close / large)
            otherwise               → 'neutral'
        """
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # equalizeHist improves detection in varying lighting
        gray  = cv2.equalizeHist(gray)
        rects = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
        )

        results = []
        for (x, y, w, h) in rects:
            face_roi = gray[y:y + h, x:x + w]

            smiles = self.smile_cascade.detectMultiScale(
                face_roi, scaleFactor=1.7, minNeighbors=20
            )
            eyes = self.eye_cascade.detectMultiScale(
                face_roi, scaleFactor=1.1, minNeighbors=5
            )

            # ── Rule-based emotion ───────────────────────────────────────────
            if len(smiles) > 0:
                emotion = 'happy'
                score   = 0.85
            elif len(eyes) == 0:
                emotion = 'sleepy'
                score   = 0.75
            elif w * h > 20_000:
                emotion = 'excited'
                score   = 0.80
            else:
                emotion = 'neutral'
                score   = 0.70

            # Build a minimal 'all' scores dict so downstream code never KeyErrors
            all_scores = {e: 0.0 for e in ('happy', 'sleepy', 'excited', 'neutral')}
            all_scores[emotion] = score

            results.append({
                'box':     [int(x), int(y), int(w), int(h)],
                'emotion': emotion,
                'base':    emotion,          # same as emotion (no extended mapping needed)
                'score':   score,
                'all':     all_scores,
            })

        return results

    # ── Hand detection ─────────────────────────────────────────────────────────
    def _detect_hands(self, frame):
        if self.hands is None:
            print("❌ hands is None — MediaPipe not loaded")
            return []
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = self.hands.process(rgb)

            if res.multi_hand_landmarks:
                print(f"🖐 Hands detected: {len(res.multi_hand_landmarks)}")
            else:
                return []

            h, w = frame.shape[:2]
            out  = []
            for i, lm_set in enumerate(res.multi_hand_landmarks):
                side = 'Right'
                if res.multi_handedness and i < len(res.multi_handedness):
                    side = res.multi_handedness[i].classification[0].label

                xs = [l.x * w for l in lm_set.landmark]
                ys = [l.y * h for l in lm_set.landmark]
                x1 = max(0, int(min(xs)) - 20)
                y1 = max(0, int(min(ys)) - 20)
                x2 = min(w, int(max(xs)) + 20)
                y2 = min(h, int(max(ys)) + 20)

                fup     = fingers_up(lm_set.landmark, side == 'Right')
                gesture = classify_hand(fup, lm_set.landmark)
                info    = HAND_GESTURES.get(
                    gesture, {'emoji': '✋', 'label': 'Hand', 'color': (148, 163, 184)}
                )

                # Normalised landmarks (0-1) for JS canvas renderer
                lm_norm = [{'x': float(l.x), 'y': float(l.y)} for l in lm_set.landmark]

                out.append({
                    'gesture':   gesture,
                    'label':     info['label'],
                    'emoji':     info['emoji'],
                    'color':     info['color'],
                    'colorHex':  _rgb_to_hex(info['color']),
                    'bbox':      [x1, y1, x2, y2],
                    'landmarks': lm_norm,
                    'side':      side,
                })
            return out

        except Exception as e:
            print(f"Hand detection error: {e}")
            return []

    # ── Draw helpers (legacy — used only by process()) ────────────────────────
    def _draw_emoji(self, frame, cx, cy, size, emoji_char):
        try:
            pil   = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
            layer = Image.new("RGBA", pil.size, (0, 0, 0, 0))
            d     = ImageDraw.Draw(layer)
            font  = get_font(size)
            bb    = d.textbbox((0, 0), emoji_char, font=font, embedded_color=True)
            ew, eh = bb[2] - bb[0], bb[3] - bb[1]
            ex, ey = cx - ew // 2, cy - eh // 2
            r = max(ew, eh) // 2 + 10
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 130))
            d.text((ex, ey), emoji_char, font=font, embedded_color=True)
            merged = Image.alpha_composite(pil, layer)
            return cv2.cvtColor(np.array(merged.convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception:
            return frame

    def _draw_face_overlay(self, frame, det):
        x, y, w, h = det['box']
        emo   = det['emotion']
        score = det['score']
        info  = EMOTIONS.get(emo, EMOTIONS['neutral'])
        color = info['color']
        cx    = x + w // 2
        cy    = y + int(h * 0.38)
        size  = max(36, min(int(w * 0.7), 120))
        frame = self._draw_emoji(frame, cx, cy, size, info['emoji'])
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = f"{emo.upper()} {int(score * 100)}%"
        font  = cv2.FONT_HERSHEY_DUPLEX
        (tw, th), _ = cv2.getTextSize(label, font, 0.55, 1)
        ov = frame.copy()
        cv2.rectangle(ov, (x, y + h + 4), (x + tw + 12, y + h + th + 14), color, -1)
        cv2.addWeighted(ov, 0.75, frame, 0.25, 0, frame)
        cv2.putText(frame, label, (x + 6, y + h + th + 10), font, 0.55,
                    (255, 255, 255), 1, cv2.LINE_AA)
        return frame

    def _draw_hand_overlay(self, frame, det):
        x1, y1, x2, y2 = det['bbox']
        color      = det['color']
        emoji_char = det['emoji']
        # Draw MediaPipe skeleton if raw landmarks were stored
        if self.hands is not None and self.mp_draw is not None and det.get('_lm_raw'):
            self.mp_draw.draw_landmarks(
                frame, det['_lm_raw'],
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=color, thickness=2, circle_radius=3),
                self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=1),
            )
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        size  = max(36, min((x2 - x1), 72))
        cx    = (x1 + x2) // 2
        cy    = max(size // 2 + 5, y1 - size // 2 - 8)
        frame = self._draw_emoji(frame, cx, cy, size, emoji_char)
        return frame

    # ── PUBLIC API ─────────────────────────────────────────────────────────────
    def process_meta(self, frame):
        """
        ★ OPTIMISED PATH — called by app.py.
        Queues frame for background AI (every 5th frame).
        Returns (faces_json, hands_json) — no image drawing at all.
        ~10-50× cheaper than process() — no PIL/OpenCV drawing, no base64 roundtrip.
        """
        self._frame_n += 1
        if self._frame_n % 5 == 0:
            with self._lock:
                small = cv2.resize(frame, (320, 240))
                self._pending = small

        with self._res_lock:
            faces = list(self._last_faces)
            hands = list(self._last_hands)

        face_out = [{
            'emotion':  d['emotion'],
            'base':     d['base'],
            'score':    float(round(d['score'], 3)),
            'emoji':    EMOTIONS.get(d['emotion'], EMOTIONS['neutral'])['emoji'],
            'colorHex': EMOTION_HEX.get(d['emotion'], '#94a3b8'),
            'box':      d['box'],
            'all':      {k: float(v) for k, v in d.get('all', {}).items()},
        } for d in faces]

        hand_out = [{
            'gesture':   d['gesture'],
            'label':     d['label'],
            'emoji':     d['emoji'],
            'colorHex':  d.get('colorHex', '#94a3b8'),
            'bbox':      d['bbox'],
            'landmarks': d.get('landmarks', []),
            'side':      d['side'],
        } for d in hands]

        return face_out, hand_out

    def process(self, frame):
        """
        Legacy path (kept for backward compatibility).
        Draws overlays onto the frame and returns (annotated_frame, faces, hands).
        """
        self._frame_n += 1
        if self._frame_n % 4 == 0:
            with self._lock:
                self._pending = frame.copy()

        with self._res_lock:
            faces = list(self._last_faces)
            hands = list(self._last_hands)

        for det in faces:
            frame = self._draw_face_overlay(frame, det)
        for det in hands:
            frame = self._draw_hand_overlay(frame, det)

        face_out = [{
            'emotion': d['emotion'],
            'base':    d['base'],
            'score':   float(round(d['score'], 3)),
            'emoji':   EMOTIONS.get(d['emotion'], EMOTIONS['neutral'])['emoji'],
            'all':     {k: float(v) for k, v in d.get('all', {}).items()},
        } for d in faces]

        hand_out = [{
            'gesture': d['gesture'],
            'label':   d['label'],
            'emoji':   d['emoji'],
            'side':    d['side'],
        } for d in hands]

        return frame, face_out, hand_out