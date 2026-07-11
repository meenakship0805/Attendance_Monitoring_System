# Attendance Monitor — Face Recognition + Liveness Detection

Face recognition attendance system with blink-based anti-spoofing, ported from a
Tkinter desktop app to Streamlit so it can be deployed and opened from a link.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Demo login: `admin` / `password`

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo.
2. Go to share.streamlit.io → New app → point it at `app.py`.
3. Done — you get a public URL to put on your resume.

**Filesystem note:** `student_data.xlsx`, `attendance_records.xlsx`, and
`trained_model.yml` are written to local disk. Streamlit Cloud's filesystem
resets on redeploy/sleep, so registered students won't persist across app
restarts. Fine for a live demo; mention it as a known limitation and the fix
(swap `core/db.py` for Supabase/Postgres) if asked in an interview.

## Why LBPH, not FaceNet/ArcFace
LBPH is fast, needs no GPU, and is a defensible choice for a small, known
population (a single classroom) rather than open-set recognition at scale.
Swapping to an embedding-based model is a real follow-on project, not a
requirement for this one — be ready to say that directly.

## Why EAR blink detection, not just face match
A face match alone can't tell a live person from a printed photo or a phone
screen. EAR (Eye Aspect Ratio) tracks whether the eyes are open or closed
across frames via MediaPipe FaceMesh landmarks — a static photo can never
register a blink. **Limitation to state up front in interviews:** this
defeats photo spoofing specifically, not a video-replay attack (playing a
recorded video of the real person blinking). That's a legitimate gap, not
something to paper over.

## Architecture
```
app.py                 # login + dashboard, Streamlit entrypoint
pages/
  1_Register_Student.py
  2_Capture_Photos.py  # browser webcam -> face samples, via WebRTC
  3_Take_Attendance.py # recognition -> liveness challenge -> mark attendance
  4_Attendance_Report.py
core/
  db.py                # Excel-backed persistence
  recognizer.py         # Haar cascade detection + LBPH train/predict
  liveness.py           # EAR calculation, frame-by-frame state tracker
webrtc_utils.py          # WebRTC video processors (recruiter's own browser camera)
```

`core/` has no Streamlit or WebRTC imports — it's plain functions/classes,
which is what makes `webrtc_utils.py` possible: the browser-frame callback
just calls into the same logic the original Tkinter loop used.

## Known deployment gotcha
Newer `mediapipe` releases (0.10.14+) dropped the legacy `mediapipe.solutions`
API this liveness code depends on. `requirements.txt` pins `mediapipe==0.10.13`
deliberately — bumping that version will break blink detection at import time.

## Interview questions to expect
- "Why webcam via WebRTC instead of OpenCV directly?" — `cv2.VideoCapture(0)`
  only sees a camera physically attached to the server; there is none on
  Streamlit Cloud. WebRTC pipes the browser's own camera to the backend.
- "How would you scale recognition past ~50 students?" — LBPH accuracy and
  speed degrade with population size; move to FaceNet/ArcFace embeddings +
  a vector index (FAISS) for open-set matching.
- "What's the actual liveness threat model?" — defeats printed photos and
  screen photos; does not defeat a video replay of the real person.
