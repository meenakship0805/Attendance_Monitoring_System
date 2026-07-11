import time
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from webrtc_utils import CaptureProcessor

st.set_page_config(page_title="Capture Face Photos", page_icon="📷")

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the home page first.")
    st.stop()

st.markdown("### 📷 CAPTURE FACE PHOTOS")
st.caption("Captures 100 grayscale face samples for the entered Student ID.")
st.divider()

sid = st.text_input("Student ID to capture for")

if sid and not sid.isdigit():
    st.error("Enter a valid numeric Student ID.")
elif sid:
    ctx = webrtc_streamer(
        key=f"capture-{sid}",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: CaptureProcessor(student_id=sid, target_count=100),
        media_stream_constraints={"video": True, "audio": False},
    )

    status = st.empty()

    # webrtc frames are processed on a background thread, so the counter on
    # the processor object only updates there — this loop is what pulls that
    # value back into the page instead of showing a stale snapshot from load.
    if ctx.state.playing:
        while ctx.state.playing:
            if ctx.video_processor:
                count = ctx.video_processor.count
                done = ctx.video_processor.done
                if done:
                    status.success(f"✓ Saved 100 photos for ID {sid}. Now go train the model on the home page.")
                    break
                else:
                    status.info(f"Capturing... {count}/100 — hold your face steady in frame")
            time.sleep(0.5)
    else:
        status.info("Click **Start** above, allow camera access, then hold your face in frame.")
else:
    st.info("Enter a Student ID above to enable the camera.")