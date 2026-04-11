"""
🎓 Faculty Dashboard – Smart Academic Monitor
A single-page Streamlit app for monitoring attendance,
tracking student performance, entering marks, and managing timetables.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time
import random

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Faculty Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS (dark-academia aesthetic)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif; letter-spacing: -0.02em; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0d1117 0%, #161b27 100%);
    border-right: 1px solid #21262d;
}
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* ── Sidebar font size ── */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] span {
    font-size: 1.1rem !important;
}
section[data-testid="stSidebar"] h3 {
    font-size: 1.4rem !important;
}

/* ── Sidebar radio buttons ── */
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 1.15rem !important;
    padding: 6px 4px !important;
}

/* ── Main background ── */
.stApp { background: #0d1117; color: #c9d1d9; }

/* ── Metric cards ── */
div[data-testid="metric-container"] {
    background: #161b27;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 16px 20px;
}

/* ── Section title ── */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    color: #e6edf3;
    border-left: 3px solid #238636;
    padding-left: 12px;
    margin: 20px 0 10px 0;
}

/* ── Timetable Grid ── */
.tt-grid {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}
.tt-grid th { background: #1c2333; color: #58a6ff; padding: 10px; border: 1px solid #21262d; }
.tt-grid td { padding: 9px 10px; border: 1px solid #21262d; text-align: center; background: #161b27; }

/* ── Form Styling ── */
div[data-testid="stForm"] {
    background: #161b27;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 20px;
}

/* ── Profile icon – top right ── */
.profile-bar {
    position: fixed;
    top: 14px;
    right: 20px;
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 10px;
    background: #161b27;
    border: 1px solid #21262d;
    border-radius: 50px;
    padding: 6px 14px 6px 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4);
    cursor: pointer;
    user-select: none;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.profile-bar:hover {
    border-color: #58a6ff;
    box-shadow: 0 4px 20px rgba(88,166,255,0.2);
}
.profile-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #238636, #58a6ff);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    font-weight: 700;
    color: #fff !important;
    flex-shrink: 0;
}
.profile-name {
    font-size: 0.88rem;
    color: #c9d1d9 !important;
    font-family: 'DM Sans', sans-serif;
    white-space: nowrap;
}
.profile-chevron {
    font-size: 0.65rem;
    color: #8b949e !important;
    margin-left: 2px;
    transition: transform 0.2s ease;
}

/* ── Profile dropdown panel ── */
.profile-dropdown {
    position: fixed;
    top: 70px;
    right: 16px;
    z-index: 9998;
    background: #1a1f2e;
    border: 1px solid #2d3448;
    border-radius: 16px;
    width: 300px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.7);
    animation: dropIn 0.22s cubic-bezier(0.4,0,0.2,1) both;
    overflow: hidden;
    font-family: 'DM Sans', sans-serif;
}
@keyframes dropIn {
    from { opacity: 0; transform: translateY(-12px) scale(0.96); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
.pd-header {
    padding: 22px 20px 16px 20px;
}
.pd-header-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff !important;
    display: block;
    margin-bottom: 4px;
}
.pd-header-role {
    font-size: 0.78rem;
    font-weight: 600;
    color: #3b9eff !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: block;
}
.pd-divider { height: 1px; background: #2d3448; margin: 0; }
.pd-body { padding: 8px 0; }
.pd-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 20px;
    transition: background 0.18s ease;
}
.pd-row:hover { background: rgba(59,158,255,0.07); }
.pd-icon {
    font-size: 1.15rem;
    width: 26px;
    text-align: center;
    flex-shrink: 0;
}
.pd-value {
    font-size: 0.92rem;
    color: #a8b3c8 !important;
    font-weight: 400;
}
.pd-manage {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 16px 20px;
    cursor: pointer;
    transition: background 0.18s ease;
    border-top: 1px solid #2d3448;
}
.pd-manage:hover { background: rgba(59,158,255,0.08); }
.pd-manage-text {
    font-size: 1rem;
    color: #ffffff !important;
    font-weight: 600;
}

/* ── Sidebar scroll smooth ── */
section[data-testid="stSidebar"] > div:first-child {
    scroll-behavior: smooth;
    transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                opacity  0.35s ease;
}

/* ── Sidebar nav item hover glow ── */
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 1.15rem !important;
    padding: 8px 12px !important;
    border-radius: 8px;
    transition: background 0.25s ease, padding-left 0.25s ease !important;
    display: block;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(88, 166, 255, 0.1) !important;
    padding-left: 18px !important;
    cursor: pointer;
}

/* ── Page content fade-in on switch ── */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0);    }
}
.page-wrapper {
    animation: fadeSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) both;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS & MOCK DATA
# ─────────────────────────────────────────────
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = [
    "09:00-10:00", "10:00-11:00", "11:00-12:00",
    "12:00-13:00", "14:00-15:00", "15:00-16:00", "16:00-17:00",
]

def _init_students():
    names = ["Aarav Sharma", "Priya Patel", "Rohan Mehta", "Neha Singh", "Karan Joshi", "Ananya Gupta"]
    students = []
    for name in names:
        total = random.randint(28, 40)
        attended = random.randint(int(total * 0.55), total)
        scores = [round(random.uniform(45, 95), 1) for _ in range(5)] # Start with 5 scores
        students.append({
            "Name": name,
            "Total Classes": total,
            "Attended Classes": attended,
            "Attendance %": round(attended / total * 100, 1),
            "Performance Score": round(np.mean(scores), 1),
            "Score History": scores,
        })
    return students

def _init_timetable():
    courses = [("Machine Learning", "Lab 201"), ("Data Structures", "Room 104")]
    timetable = {day: {slot: None for slot in TIME_SLOTS} for day in DAYS}
    for day in DAYS:
        for slot in TIME_SLOTS:
            if random.random() > 0.5:
                course, room = random.choice(courses)
                timetable[day][slot] = {"course": course, "room": room}
    return timetable

def _ensure_state():
    if "students_data" not in st.session_state:
        st.session_state.students_data = _init_students()
    if "timetable_data" not in st.session_state:
        st.session_state.timetable_data = _init_timetable()
    if "selected_student" not in st.session_state:
        st.session_state.selected_student = st.session_state.students_data[0]["Name"]
    if "profile_open" not in st.session_state:
        st.session_state.profile_open = False

# ─────────────────────────────────────────────
# MODULE A – ATTENDANCE DASHBOARD
# ─────────────────────────────────────────────
def render_attendance_dashboard():
    st.markdown('<p class="section-title">📋 Attendance Dashboard</p>', unsafe_allow_html=True)
    df = pd.DataFrame([{k: v for k, v in s.items() if k != "Score History"} for s in st.session_state.students_data])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total Students", len(df))
    c2.metric("📊 Avg Attendance", f"{df['Attendance %'].mean():.1f}%")
    c3.metric("⚠️ At-Risk (<75%)", len(df[df["Attendance %"] < 75]))
    
    st.dataframe(df.style.map(lambda x: "color: #f85149" if isinstance(x, float) and x < 75 else "", subset=["Attendance %"]), use_container_width=True)

# ─────────────────────────────────────────────
# MODULE B – PERFORMANCE TRACKER
# ─────────────────────────────────────────────
def render_student_performance():
    st.markdown('<p class="section-title">📈 Student Performance Tracker</p>', unsafe_allow_html=True)
    names = [s["Name"] for s in st.session_state.students_data]
    chosen = st.selectbox("Select Student", names, key="perf_select")
    
    student = next(s for s in st.session_state.students_data if s["Name"] == chosen)
    
    k1, k2 = st.columns(2)
    k1.metric("🎯 Current Grade Avg", f"{student['Performance Score']}/100")
    k2.metric("📝 Exams Taken", len(student["Score History"]))
    
    chart_df = pd.DataFrame({"Score": student["Score History"]})
    st.line_chart(chart_df)

# ─────────────────────────────────────────────
# MODULE C – MARKS ENTRY (NEW FEATURE)
# ─────────────────────────────────────────────
def render_marks_entry():
    st.markdown('<p class="section-title">📝 Marks Entry Portal</p>', unsafe_allow_html=True)
    
    exam_type = st.selectbox("Assessment Type", ["Quiz", "Midterm", "End-term", "Assignment"])
    
    st.info("Enter the new scores below and click Submit to update the database.")
    
    with st.form("marks_entry_form"):
        col_n, col_l, col_i = st.columns([2, 1, 1])
        col_n.markdown("**Student Name**")
        col_l.markdown("**Last Score**")
        col_i.markdown("**New Score**")
        
        new_entries = {}
        for i, student in enumerate(st.session_state.students_data):
            c_name, c_last, c_input = st.columns([2, 1, 1])
            c_name.write(student["Name"])
            c_last.write(student["Score History"][-1] if student["Score History"] else "N/A")
            new_entries[student["Name"]] = c_input.number_input(f"Score for {student['Name']}", 0.0, 100.0, step=1.0, label_visibility="collapsed", key=f"score_{i}")
        
        if st.form_submit_button("🚀 Submit & Update Records"):
            for student in st.session_state.students_data:
                score = new_entries[student["Name"]]
                student["Score History"].append(score)
                # Recalculate average
                student["Performance Score"] = round(np.mean(student["Score History"]), 1)
            
            st.success(f"Successfully added marks for {exam_type}!")
            st.balloons()

# ─────────────────────────────────────────────
# MODULE D – TIMETABLE
# ─────────────────────────────────────────────
def render_timetable():
    st.markdown('<p class="section-title">📅 Class Timetable</p>', unsafe_allow_html=True)
    # Simple grid logic for brevity
    st.write("Weekly Schedule Grid")
    tt_df = pd.DataFrame(st.session_state.timetable_data).T
    st.table(tt_df.map(lambda x: x['course'] if x else "—"))

# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────
def main():
    _ensure_state()

    # ── Profile toggle button (top-right via columns trick) ──
    _, col_btn = st.columns([11, 1])
    with col_btn:
        if st.button("DS", key="profile_toggle", help="View profile"):
            st.session_state.profile_open = not st.session_state.profile_open

    # ── Inject CSS to style that button as a circular avatar ──
    st.markdown("""
    <style>
    /* Make the profile toggle button a blue circle like the image */
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child button {
        width: 46px !important;
        height: 46px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #1a6ed8, #3b9eff) !important;
        color: #fff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border: none !important;
        cursor: pointer !important;
        box-shadow: 0 2px 14px rgba(58,158,255,0.45) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        padding: 0 !important;
        min-height: unset !important;
        line-height: 1 !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child button:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 4px 22px rgba(58,158,255,0.6) !important;
    }
    /* Hide the button label border/outline */
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child button:focus {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(58,158,255,0.35) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Profile dropdown card ──
    if st.session_state.profile_open:
        st.markdown("""
        <div class="profile-dropdown">
            <div class="pd-header">
                <span class="pd-header-name">Dr. Smith</span>
                <span class="pd-header-role">Computer Science</span>
            </div>
            <div class="pd-divider"></div>
            <div class="pd-body">
                <div class="pd-row">
                    <span class="pd-icon">🎓</span>
                    <span class="pd-value">Faculty ID: FAC-CS-2024</span>
                </div>
                <div class="pd-row">
                    <span class="pd-icon">✉️</span>
                    <span class="pd-value">dr.smith@university.edu</span>
                </div>
                <div class="pd-row">
                    <span class="pd-icon">📱</span>
                    <span class="pd-value">+91 98765 43210</span>
                </div>
            </div>
            <div class="pd-divider"></div>
            <div class="pd-manage">
                <span style="font-size:1.2rem;">⚙️</span>
                <span class="pd-manage-text">Manage Account</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; margin-top: -2rem;'>🎓 Faculty Dashboard</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🎓 Navigation")
        page = st.radio(
            "Go to:",
            [
                "📋  Attendance",
                "📈  Performance",
                "📝  Marks Entry",
                "📅  Timetable",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("👤 Logged in as: **Dr. Smith**")
        st.markdown(f"📆 Date: **{datetime.now().strftime('%d %b %Y')}**")

    # ── Wrap active page in fade-slide animation ──
    st.markdown('<div class="page-wrapper">', unsafe_allow_html=True)
    if "Attendance" in page:
        render_attendance_dashboard()
    elif "Performance" in page:
        render_student_performance()
    elif "Marks Entry" in page:
        render_marks_entry()
    else:
        render_timetable()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()