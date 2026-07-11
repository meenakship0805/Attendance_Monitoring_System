"""
webrtc_utils.py — Browser-camera video processors for streamlit-webrtc.

This is the piece that didn't exist in the desktop version. cv2.VideoCapture(0)
only sees a camera physically attached to the machine RUNNING the code — on
Streamlit Cloud that's Streamlit's server, which has no camera. streamlit-webrtc
instead pipes frames from the RECRUITER'S browser (their webcam) over WebRTC into
a VideoProcessorBase.recv() callback that runs once per frame and must return
quickly — so both processors below are non-blocking state machines instead of
the original's blocking while-loops.
"""

import time
import cv2
import av
from streamlit_webrtc import VideoProcessorBase

from core.recognizer import detect_faces, recognize_face_in_frame, save_face_sample
from core.liveness import LivenessTracker
from core.db import mark_attendance

GREEN = (62, 207, 142)
RED = (240, 110, 110)
BLUE = (247, 142, 79)  # BGR


class CaptureProcessor(VideoProcessorBase):
    """Used on the registration page to save N face samples for one student."""

    def __init__(self, student_id, target_count=100):
        self.student_id = student_id
        self.target_count = target_count
        self.count = 0
        self.done = False

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        if not self.done:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            for (x, y, w, h) in detect_faces(img):
                roi = gray[y:y + h, x:x + w]
                save_face_sample(self.student_id, roi, self.count)
                self.count += 1
                cv2.rectangle(img, (x, y), (x + w, y + h), BLUE, 2)
                break  # one face per frame is enough
            if self.count >= self.target_count:
                self.done = True

        cv2.putText(img, f"Captured: {self.count}/{self.target_count}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, BLUE, 2)
        if self.done:
            cv2.putText(img, "Done - you can stop the camera",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, GREEN, 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")


class AttendanceProcessor(VideoProcessorBase):
    """
    State machine per browser session:
      SCANNING  -> looking for a recognisable, not-yet-marked face
      LIVENESS  -> a face was recognised, waiting for a confirmed blink
    `events` is a list the Streamlit page polls to render a log + toasts,
    since recv() runs on a background thread and can't call st.* directly.
    """

    def __init__(self):
        self.state = "SCANNING"
        self.current_sid = None
        self.current_name = None
        self.tracker = None
        self.marked_ids = set()
        self.events = []

    def _log(self, kind, name, sid):
        self.events.append({"kind": kind, "name": name, "sid": sid, "ts": time.time()})

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        if self.state == "SCANNING":
            for (x, y, w, h) in detect_faces(img):
                gray_roi = cv2.cvtColor(img[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
                sid, name, conf = recognize_face_in_frame(gray_roi)
                color = GREEN if sid else RED
                cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img, f"{name} ({conf:.0f})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                if sid and sid not in self.marked_ids:
                    self.state = "LIVENESS"
                    self.current_sid = sid
                    self.current_name = name
                    self.tracker = LivenessTracker()
                    self._log("recognised", name, sid)
                break  # handle one face at a time

        elif self.state == "LIVENESS":
            blinked = self.tracker.update(img)
            remaining = self.tracker.seconds_remaining()

            cv2.putText(img, f"BLINK to confirm ({remaining}s)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, BLUE, 2)
            if self.tracker.last_ear is not None:
                cv2.putText(img, f"EAR: {self.tracker.last_ear:.2f}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLUE, 1)

            if blinked:
                ok = mark_attendance(self.current_sid, self.current_name)
                self._log("marked" if ok else "duplicate", self.current_name, self.current_sid)
                self.marked_ids.add(self.current_sid)
                self.tracker.close()
                self.state = "SCANNING"
            elif self.tracker.timed_out():
                self._log("rejected", self.current_name, self.current_sid)
                # short cooldown: still mark as "seen" for 1 pass so it doesn't
                # instantly re-trigger every frame; recruiter can step back in frame
                self.marked_ids.add(self.current_sid)
                self.tracker.close()
                self.state = "SCANNING"

        return av.VideoFrame.from_ndarray(img, format="bgr24")
