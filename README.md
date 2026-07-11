Attendance Monitor — Face Recognition + Liveness Detection

Live demo: https://attendancemonitoringsystem-nsrd2bx5skzyikq5heyk7p.streamlit.app/
Demo login: admin / password

Face recognition attendance system with blink-based anti-spoofing, ported from a
Tkinter desktop app to Streamlit so it can be deployed and opened from a link.

Run locally

Requires Python 3.11 specifically — mediapipe's legacy solutions API
(used for blink detection) isn't yet available for newer Python releases.

bashpy -3.11 -m venv venv
venv\Scripts\activate      # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
streamlit run app.py

Deploy (Streamlit Community Cloud)


Push this folder to a GitHub repo.
Go to share.streamlit.io → New app → point it at app.py.
Streamlit Cloud reads runtime.txt (pins Python 3.11) and packages.txt
(system libraries OpenCV needs) automatically — no manual config needed.


Filesystem note: student_data.xlsx, attendance_records.xlsx, and
trained_model.yml are written to local disk. Streamlit Cloud's filesystem
resets on redeploy/sleep, so registered students won't persist across app
restarts. Fine for a live demo; mention it as a known limitation and the fix
(swap core/db.py for Supabase/Postgres) if asked in an interview.

Why LBPH, not FaceNet/ArcFace

LBPH is fast, needs no GPU, and is a defensible choice for a small, known
population (a single classroom) rather than open-set recognition at scale.
Swapping to an embedding-based model is a real follow-on project, not a
requirement for this one — be ready to say that directly.

Why EAR blink detection, not just face match

A face match alone can't tell a live person from a printed photo or a phone
screen. EAR (Eye Aspect Ratio) tracks whether the eyes are open or closed
across frames via MediaPipe FaceMesh landmarks — a static photo can never
register a blink. Limitation to state up front in interviews: this
defeats photo spoofing specifically, not a video-replay attack (playing a
recorded video of the real person blinking). That's a legitimate gap, not
something to paper over.

Architecture

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
  haarcascade_frontalface_default.xml  # bundled directly (see note below)
webrtc_utils.py          # WebRTC video processors (recruiter's own browser camera)
runtime.txt               # pins Python 3.11 for Streamlit Cloud
packages.txt               # system libraries (see deployment gotchas below)

core/ has no Streamlit or WebRTC imports — it's plain functions/classes,
which is what makes webrtc_utils.py possible: the browser-frame callback
just calls into the same logic the original Tkinter loop used.

Deployment gotchas actually hit while building this

Real issues found while getting this from "works on my machine" to a public
URL — good material for "tell me about a bug you debugged" in interviews:


Python 3.14 incompatibility. mediapipe has no wheel for very new
Python releases yet. Fixed by pinning Python 3.11 via runtime.txt
(locally, via a separate venv built with py -3.11).
mediapipe's legacy solutions API was removed in mediapipe 0.10.14+.
requirements.txt pins mediapipe==0.10.13 deliberately — bumping that
version silently breaks blink detection at import time, not at runtime.
Dual-opencv conflict. mediapipe depends on opencv-contrib-python
internally; listing opencv-python-headless separately in
requirements.txt installs two competing cv2 packages, corrupting the
import. Fix: don't list opencv separately at all — let mediapipe pull
its own.
opencv-contrib-python is a GUI-capable build, so on a headless Linux
server it needs system libraries (libGL, libglib) that aren't there
by default. packages.txt installs libgl1 and libglib2.0-0t64
(the t64 suffix is the renamed package on Debian trixie's 64-bit time
transition — plain libglib2.0-0 fails on Streamlit Cloud's current base
image).
cv2.data.haarcascades is unreliable across opencv wheel builds —
some don't bundle the XML data files at all. Fixed by bundling
haarcascade_frontalface_default.xml directly in core/ and loading it
by explicit relative path instead of trusting the package's bundled data.