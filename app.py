import streamlit as st
from core.recognizer import load_model_if_exists

st.set_page_config(
    page_title="Attendance Monitor",
    page_icon="◈",
    layout="centered",
)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"  

load_model_if_exists()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login_screen():
    st.markdown("### ◈ ATTENDANCE MONITOR")
    st.caption("face recognition + liveness detection")
    st.divider()

    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login →", use_container_width=True)

    if submitted:
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.info("Demo credentials — username: `admin`, password: `password`", icon="ℹ️")


def dashboard():
    st.markdown("### ◈ DASHBOARD")
    st.caption(
        "Use the pages in the sidebar to register students, capture face "
        "samples, take attendance, and view reports."
    )
    st.divider()
    st.markdown(
        "**How it works:**\n"
        "1. Register a student and capture their face samples\n"
        "2. Train the model (button below)\n"
        "3. Take attendance — camera recognises the face, then asks for a blink\n"
        "4. A blink confirms a live person; a static photo can't blink, so it's rejected"
    )

    if st.button("🧠 Train Model", use_container_width=True):
        from core.recognizer import train_and_save_model
        ok, msg = train_and_save_model()
        (st.success if ok else st.error)(msg)

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()


if not st.session_state.logged_in:
    login_screen()
else:
    dashboard()
