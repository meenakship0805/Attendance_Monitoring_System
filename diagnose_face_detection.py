import os
import cv2

_CASCADE_PATH = os.path.join(os.path.dirname(__file__), "core", "haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(_CASCADE_PATH)
if face_cascade.empty():
    print(f"ERROR: failed to load cascade from {_CASCADE_PATH}")
    exit(1)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: could not open webcam. Is it in use by another app (like the Streamlit tab)?")
    exit(1)

print("Press SPACE to test the current frame, Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: could not read frame from webcam.")
        break

    cv2.imshow("Live feed - press SPACE to test, Q to quit", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key == 32:  # SPACE
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        print(f"\nFaces detected: {len(faces)}")
        print(f"Average brightness (0-255, aim for 80-180): {gray.mean():.1f}")

        result = frame.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 3)

        cv2.imwrite("diagnostic_result.jpg", result)
        print("Saved diagnostic_result.jpg — open it and check for a green box around your face.\n")

cap.release()
cv2.destroyAllWindows()