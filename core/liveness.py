"""
core/liveness.py — EAR (Eye Aspect Ratio) blink-based liveness detection.

The original desktop version used a blocking `while` loop with
cv2.imshow() to wait for a blink. That doesn't work over WebRTC — the
browser sends one frame at a time to a callback that must return
immediately. So the same EAR math is kept, but reorganised into a
LivenessTracker object that holds its state (deadline, consecutive-frame
counter, blink flag) BETWEEN calls, and gets fed one frame per call.

Why EAR blink detection works as liveness proof:
  A printed photo or a phone/laptop screen showing a photo cannot blink.
  A video replay attack (playing a video of the person) technically could
  fool this, which is the real limitation — EAR blink detection defeats
  static-photo spoofing specifically, not video replay attacks. Mention
  that limitation directly if asked in an interview; it's the correct
  answer, not a weakness to hide.
"""

import math
import time

try:
    import mediapipe as mp
    MP_AVAILABLE = True
    _mp_face_mesh = mp.solutions.face_mesh
except ImportError:
    MP_AVAILABLE = False

EAR_THRESHOLD = 0.22
EAR_CONSEC_FRAMES = 2
BLINK_TIMEOUT_SEC = 8

LEFT_EYE_IDX = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_IDX = [33, 160, 158, 133, 153, 144]


def _eye_aspect_ratio(landmarks, eye_indices, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_indices]

    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    vert1 = dist(pts[1], pts[5])
    vert2 = dist(pts[2], pts[4])
    horiz = dist(pts[0], pts[3])
    return (vert1 + vert2) / (2.0 * horiz) if horiz > 0 else 0


class LivenessTracker:
    """One instance per liveness challenge (i.e. per recognised face)."""

    def __init__(self):
        self.face_mesh = (
            _mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            if MP_AVAILABLE else None
        )
        self.deadline = time.time() + BLINK_TIMEOUT_SEC
        self.consec = 0
        self.blink_detected = False
        self.last_ear = None

    def timed_out(self):
        return time.time() > self.deadline

    def seconds_remaining(self):
        return max(0, int(self.deadline - time.time()))

    def update(self, bgr_frame):
        """Feed one frame in. Returns True the instant a blink is confirmed."""
        if self.blink_detected or not MP_AVAILABLE:
            return self.blink_detected

        import cv2  # local import keeps this module importable without cv2 in tests
        h, w = bgr_frame.shape[:2]
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        if not result.multi_face_landmarks:
            return False

        lm = result.multi_face_landmarks[0].landmark
        left_ear = _eye_aspect_ratio(lm, LEFT_EYE_IDX, w, h)
        right_ear = _eye_aspect_ratio(lm, RIGHT_EYE_IDX, w, h)
        self.last_ear = (left_ear + right_ear) / 2.0

        if self.last_ear < EAR_THRESHOLD:
            self.consec += 1
        else:
            if self.consec >= EAR_CONSEC_FRAMES:
                self.blink_detected = True
            self.consec = 0

        return self.blink_detected

    def close(self):
        if self.face_mesh:
            self.face_mesh.close()
