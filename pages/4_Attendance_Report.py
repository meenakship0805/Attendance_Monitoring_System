from datetime import date
import streamlit as st
from core.db import get_attendance_records

st.set_page_config(page_title="Attendance Report", page_icon="📊")

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the home page first.")
    st.stop()

st.markdown("### 📊 ATTENDANCE REPORT")
st.divider()

col1, col2 = st.columns([2, 1])
filter_date = col1.date_input("Filter by date", value=date.today())
show_all = col2.checkbox("Show all dates")

df = get_attendance_records(None if show_all else filter_date.isoformat())

st.dataframe(df, use_container_width=True, hide_index=True)
st.caption(f"{len(df)} record(s) shown")

if not df.empty:
    st.download_button(
        "⬇️ Export CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"attendance_{filter_date.isoformat() if not show_all else 'all'}.csv",
        mime="text/csv",
        use_container_width=True,
    )
