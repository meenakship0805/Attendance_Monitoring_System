"""
core/recognizer.py — Face detection, LBPH training, and recognition.

Pulled directly from the original Tkinter app's logic. LBPH is kept
deliberately — swapping to FaceNet/ArcFace is a real project on its own,
not a cleanup task, and LBPH is a perfectly defensible choice to explain
in an interview: fast, no GPU needed, works well on a small enrolled
population like a classroom.
"""

import os
import cv2
import numpy as np

from core.db import get_student_name

PHOTOS_DIR = "student_photos"
MODEL_FILE = "trained_model.yml"
CONFIDENCE_THRESH = 60          # lower = stricter recognition
PHOTOS_PER_STUDENT = 100

_CASCADE_PATH = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(_CASCADE_PATH)
if face_cascade.empty():
    raise RuntimeError(
        f"Failed to load face cascade from {_CASCADE_PATH} — file missing or corrupt."
    )
recognizer = cv2.face.LBPHFaceRecognizer_create()
model_trained = False


def load_model_if_exists():
    global model_trained
    if os.path.exists(MODEL_FILE):
        recognizer.read(MODEL_FILE)
        model_trained = True
    return model_trained


def is_model_trained():
    return model_trained


def detect_faces(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )


def save_face_sample(student_id, gray_roi, index):
    student_dir = os.path.join(PHOTOS_DIR, str(student_id))
    os.makedirs(student_dir, exist_ok=True)
    cv2.imwrite(os.path.join(student_dir, f"{index}.jpg"), gray_roi)


def load_training_data():
    samples, labels = [], []
    if not os.path.exists(PHOTOS_DIR):
        return samples, labels
    for person in os.listdir(PHOTOS_DIR):
        person_dir = os.path.join(PHOTOS_DIR, person)
        if not os.path.isdir(person_dir):
            continue
        try:
            label = int(person)
        except ValueError:
            continue
        for fname in os.listdir(person_dir):
            img = cv2.imread(os.path.join(person_dir, fname), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                samples.append(img)
                labels.append(label)
    return samples, labels


def train_and_save_model():
    global model_trained
    samples, labels = load_training_data()
    if not samples:
        return False, "No training data found. Capture photos first."
    recognizer.train(samples, np.array(labels))
    recognizer.save(MODEL_FILE)
    model_trained = True
    return True, f"Model trained on {len(samples)} images from {len(set(labels))} students."


def recognize_face_in_frame(gray_roi):
    """Returns (student_id or None, name, confidence)."""
    if not model_trained:
        return None, "No Model", 0
    try:
        sid, conf = recognizer.predict(gray_roi)
        if conf < CONFIDENCE_THRESH:
            return sid, get_student_name(sid), conf
    except Exception:
        pass
    return None, "Unknown", 0
