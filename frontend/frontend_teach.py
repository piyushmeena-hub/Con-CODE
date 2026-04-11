import streamlit as st
import pandas as pd
import requests
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE_URL}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        st.error("❌ Backend Offline on Port 8000")
        return None

def api_post(path: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        st.error("❌ Backend Offline on Port 8000")
        return None

st.set_page_config(page_title="Faculty Dashboard", page_icon="🎓", layout="wide")

# (Keep your existing st.markdown CSS block here - omitted for brevity)

def _ensure_state():
    if "profile_open" not in st.session_state: st.session_state.profile_open = False
    if "students_data" not in st.session_state: st.session_state.students_data = None

def _get_students():
    if st.session_state.students_data is None:
        raw = api_get("/faculty/me/dashboard")
        if raw:
            st.session_state.students_data = [
                {"student_id": s["student_id"], "Name": s["name"], "Total Classes": s["total_classes"],
                 "Attended Classes": s["attended_classes"], "Attendance %": s["attendance_percentage"],
                 "Performance Score": s["performance_score"], "Score History": s["score_history"]}
                for s in raw
            ]
    return st.session_state.students_data or []

def render_attendance_dashboard():
    st.markdown('<p class="section-title">📋 Attendance Dashboard</p>', unsafe_allow_html=True)
    students = _get_students()
    if students:
        df = pd.DataFrame([{k: v for k, v in s.items() if k != "Score History"} for s in students])
        c1, c2, c3 = st.columns(3)
        c1.metric("👥 Total Students", len(df))
        c2.metric("📊 Avg Attendance", f"{df['Attendance %'].mean():.1f}%")
        c3.metric("⚠️ At-Risk (<75%)", len(df[df["Attendance %"] < 75]))
        st.dataframe(df.drop(columns=["student_id"]), use_container_width=True)

def render_student_performance():
    st.markdown('<p class="section-title">📈 Performance Tracker</p>', unsafe_allow_html=True)
    students = _get_students()
    if students:
        chosen = st.selectbox("Select Student", [s["Name"] for s in students])
        student = next(s for s in students if s["Name"] == chosen)
        st.metric("🎯 Average Grade", f"{student['Performance Score']}/100")
        st.line_chart(pd.DataFrame({"Score": student["Score History"]}))

def render_marks_entry():
    st.markdown('<p class="section-title">📝 Marks Entry Portal</p>', unsafe_allow_html=True)
    students = _get_students()
    if students:
        exam = st.selectbox("Type", ["Quiz", "Midterm", "Final"])
        with st.form("marks_form"):
            new_scores = {}
            for s in students:
                new_scores[s["student_id"]] = st.number_input(f"Score for {s['Name']}", 0.0, 100.0, key=f"m_{s['student_id']}")
            if st.form_submit_button("🚀 Submit"):
                payload = {"assessment_type": exam, "course_id": 1, "marks": [{"student_id": k, "score": v} for k, v in new_scores.items()]}
                if api_post("/assessments/marks/bulk", payload):
                    st.success("Marks Updated!")
                    st.session_state.students_data = None

def render_manage_records():
    st.markdown('<p class="section-title">⚙️ Manage Academic Session</p>', unsafe_allow_html=True)
    st.subheader("Register New Student")
    with st.form("reg_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        total = st.number_input("Total Classes", 1, 100, 40)
        if st.form_submit_button("➕ Register"):
            if name and api_post("/students", {"name": name, "total_classes": int(total)}):
                st.success(f"Registered {name}!")
                st.session_state.students_data = None

def main():
    _ensure_state()
    with st.sidebar:
        st.markdown("### 🎓 Navigation")
        page = st.radio("Go to:", ["📋 Attendance", "📈 Performance", "📝 Marks Entry", "📅 Timetable", "⚙️ Manage Records"], label_visibility="collapsed")
    
    if "Attendance" in page: render_attendance_dashboard()
    elif "Performance" in page: render_student_performance()
    elif "Marks Entry" in page: render_marks_entry()
    elif "Manage Records" in page: render_manage_records()
    else: st.write("📅 Timetable Content Here") # Re-add your timetable logic as needed

if __name__ == "__main__":
    main()
