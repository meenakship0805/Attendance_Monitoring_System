import time
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from webrtc_utils import AttendanceProcessor
from core.recognizer import is_model_trained

st.set_page_config(page_title="Take Attendance", page_icon="✅")

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the home page first.")
    st.stop()

st.markdown("### ✅ TAKE ATTENDANCE")
st.caption("🛡 liveness check ON — a printed photo cannot blink, so it gets rejected.")
st.divider()

if not is_model_trained():
    st.warning("No trained model found. Register students, capture photos, then train the model from the home page.")
    st.stop()

st.markdown(
    "**How it works:**\n"
    "1. Stand in front of the camera\n"
    "2. System recognises your face\n"
    "3. Blink to confirm you're live — a photo held up to the camera can't blink\n"
    "4. Attendance is marked only after a confirmed blink"
)
st.divider()

ctx = webrtc_streamer(
    key="attendance",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=AttendanceProcessor,
    media_stream_constraints={"video": True, "audio": False},
)

log_placeholder = st.empty()

ICONS = {"recognised": "👤", "marked": "✅", "duplicate": "⚠️", "rejected": "🚫"}
LABELS = {
    "recognised": "recognised — starting liveness check",
    "marked": "LIVE ✓ — attendance marked",
    "duplicate": "already marked today",
    "rejected": "NO BLINK detected — rejected (possible spoof)",
}

if ctx.state.playing:
    # recv() runs on a background thread and appends to processor.events there;
    # this loop is what actually pulls new events back into the visible page.
    last_count = -1
    while ctx.state.playing:
        if ctx.video_processor:
            events = ctx.video_processor.events[-10:]
            if len(events) != last_count:
                last_count = len(events)
                if events:
                    lines = []
                    for e in reversed(events):
                        ts = time.strftime("%H:%M:%S", time.localtime(e["ts"]))
                        lines.append(f"`{ts}` {ICONS[e['kind']]} **{e['name']}** (ID {e['sid']}) — {LABELS[e['kind']]}")
                    log_placeholder.markdown("\n\n".join(lines))
                else:
                    log_placeholder.info("Camera active — step in front of the camera...")
        time.sleep(0.5)
else:
    log_placeholder.info("Press **Start** above to begin.")