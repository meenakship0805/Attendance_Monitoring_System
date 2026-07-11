import streamlit as st
from core.db import add_student_to_excel, get_all_students

st.set_page_config(page_title="Register Student", page_icon="👤")

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the home page first.")
    st.stop()

st.markdown("### 👤 STUDENT MANAGEMENT")
st.divider()

with st.form("add_student", clear_on_submit=True):
    col1, col2 = st.columns(2)
    sid = col1.text_input("Student ID (numeric)")
    name = col2.text_input("Full Name")
    col3, col4 = st.columns(2)
    age = col3.text_input("Age")
    gender = col4.selectbox("Gender", ["M", "F", "Other"])
    submitted = st.form_submit_button("➕ Add Student", use_container_width=True)

if submitted:
    if not sid or not name:
        st.error("ID and Name are required.")
    elif not sid.isdigit():
        st.error("Student ID must be numeric.")
    else:
        ok, msg = add_student_to_excel(sid, name, age, gender)
        (st.success if ok else st.error)(msg)

st.divider()
st.markdown("**Registered Students**")
st.dataframe(get_all_students(), use_container_width=True, hide_index=True)

st.info("Next: go to **Capture Photos** to record this student's face samples.", icon="➡️")
