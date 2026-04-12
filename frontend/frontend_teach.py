"""
🎓 Faculty Dashboard – Smart Academic Monitor
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

API_BASE_URL  = "http://localhost:8000/api/v1"
LOGIN_PAGE_URL = "http://localhost:5000/login/teacher"

# ─────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────
def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE_URL}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Backend offline — run `python main.py` on port 8000.")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_post(path: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Backend offline — run `python main.py` on port 8000.")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None

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
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif; letter-spacing: -0.02em; }
.stApp { background: #0d1117; color: #c9d1d9; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0d1117 0%, #161b27 100%);
    border-right: 1px solid #21262d;
}
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] span { font-size: 1.1rem !important; }
section[data-testid="stSidebar"] h3 { font-size: 1.4rem !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 1.15rem !important; padding: 8px 12px !important;
    border-radius: 8px;
    transition: background 0.25s ease, padding-left 0.25s ease !important;
    display: block;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(88,166,255,0.1) !important;
    padding-left: 18px !important;
}

/* ── Metric cards ── */
div[data-testid="metric-container"] {
    background: #161b27; border: 1px solid #21262d;
    border-radius: 12px; padding: 16px 20px;
}

/* ── Section title ── */
.section-title {
    font-family: 'Playfair Display', serif; font-size: 1.4rem;
    color: #e6edf3; border-left: 3px solid #238636;
    padding-left: 12px; margin: 20px 0 16px 0;
}

/* ── Form ── */
div[data-testid="stForm"] {
    background: #161b27; border: 1px solid #21262d;
    border-radius: 12px; padding: 20px;
}

/* ── Timetable grid ── */
.tt-wrap { overflow-x: auto; margin-top: 8px; }
table.tt {
    width: 100%; border-collapse: collapse;
    font-family: 'DM Sans', sans-serif; font-size: 0.85rem;
}
table.tt th {
    background: #1c2333; color: #58a6ff; font-weight: 700;
    padding: 12px 14px; border: 1px solid #21262d;
    text-align: center; white-space: nowrap;
}
table.tt td {
    padding: 10px 14px; border: 1px solid #21262d;
    text-align: center; background: #161b27; color: #c9d1d9;
    vertical-align: middle;
}
table.tt td.time-col {
    background: #1c2333; color: #8b949e;
    font-weight: 600; white-space: nowrap;
}
table.tt td.has-class {
    background: #0d2137;
}
.class-pill {
    display: inline-block;
    background: linear-gradient(135deg, #1a6ed8, #238636);
    color: #fff !important; border-radius: 8px;
    padding: 5px 10px; font-size: 0.78rem; font-weight: 600;
    line-height: 1.4;
}
.room-tag {
    display: block; font-size: 0.7rem;
    color: #8b949e; margin-top: 3px;
}

/* ── Profile dropdown ── */
.profile-dropdown {
    position: fixed; top: 70px; right: 16px; z-index: 9998;
    background: #1a1f2e; border: 1px solid #2d3448;
    border-radius: 16px; width: 300px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.7);
    animation: dropIn 0.22s cubic-bezier(0.4,0,0.2,1) both;
    overflow: hidden;
}
@keyframes dropIn {
    from { opacity: 0; transform: translateY(-12px) scale(0.96); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
.pd-header { padding: 22px 20px 16px 20px; }
.pd-header-name { font-size: 1.25rem; font-weight: 700; color: #fff !important; display: block; margin-bottom: 4px; }
.pd-header-role { font-size: 0.78rem; font-weight: 600; color: #3b9eff !important; letter-spacing: 0.08em; text-transform: uppercase; display: block; }
.pd-divider { height: 1px; background: #2d3448; }
.pd-body { padding: 8px 0; }
.pd-row { display: flex; align-items: center; gap: 14px; padding: 11px 20px; transition: background 0.18s ease; }
.pd-row:hover { background: rgba(59,158,255,0.07); }
.pd-icon { font-size: 1.1rem; width: 24px; text-align: center; flex-shrink: 0; }
.pd-value { font-size: 0.9rem; color: #a8b3c8 !important; }
.pd-manage { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 15px 20px; border-top: 1px solid #2d3448; cursor: pointer; transition: background 0.18s ease; }
.pd-manage:hover { background: rgba(59,158,255,0.08); }
.pd-manage-text { font-size: 1rem; color: #fff !important; font-weight: 600; }

/* ── Avatar button ── */
div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child button {
    width: 46px !important; height: 46px !important; border-radius: 50% !important;
    background: linear-gradient(135deg, #1a6ed8, #3b9eff) !important;
    color: #fff !important; font-weight: 700 !important; font-size: 0.95rem !important;
    border: none !important; padding: 0 !important; min-height: unset !important;
    box-shadow: 0 2px 14px rgba(58,158,255,0.45) !important;
    transition: transform 0.15s ease !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child button:hover {
    transform: scale(1.1) !important;
}

/* ── Page fade-in ── */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.page-wrapper { animation: fadeSlideIn 0.35s cubic-bezier(0.4,0,0.2,1) both; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTH GUARD
# ─────────────────────────────────────────────
def _check_auth() -> bool:
    """
    Reads ?user= and ?role= set by the Flask login redirect.
    Stores them in session state so subsequent reruns don't need the params.
    Shows a login wall if neither is present.
    """
    if st.session_state.get("authenticated"):
        return True

    # Pick up query params on first load after redirect
    user = st.query_params.get("user", "")
    role = st.query_params.get("role", "")

    if user and role:
        st.session_state.authenticated  = True
        st.session_state.auth_username  = user
        st.session_state.auth_role      = role
        st.query_params.clear()
        return True

    # Not authenticated — show redirect wall
    st.markdown(f"""
    <style>
    .stApp {{ background: #09090b; }}
    .auth-wall {{
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; height: 80vh; gap: 20px;
        font-family: 'Inter', sans-serif;
    }}
    .auth-wall h2 {{ color: #fff; font-size: 1.8rem; margin: 0; }}
    .auth-wall p  {{ color: #94a3b8; margin: 0; }}
    .auth-btn {{
        display: inline-block; padding: 12px 32px;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white; border-radius: 50px; font-weight: 700;
        font-size: 1rem; text-decoration: none;
        box-shadow: 0 5px 15px rgba(37,99,235,0.4);
    }}
    </style>
    <div class="auth-wall">
        <h2>🎓 Faculty Dashboard</h2>
        <p>Please log in to continue.</p>
        <a class="auth-btn" href="{LOGIN_PAGE_URL}" target="_self">Go to Login →</a>
    </div>
    """, unsafe_allow_html=True)
    st.stop()
    return False


def _ensure_state():
    defaults = {
        "profile_open":   False,
        "students_data":  None,
        "timetable_data": None,
        "fac_profile":    None,
        "authenticated":  False,
        "auth_token":     "",
        "auth_username":  "",
        "auth_role":      "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _get_faculty() -> dict:
    if st.session_state.fac_profile is None:
        st.session_state.fac_profile = api_get("/faculty/me") or {}
    return st.session_state.fac_profile

def _get_students() -> list:
    if st.session_state.students_data is None:
        raw = api_get("/faculty/me/dashboard")
        if raw:
            st.session_state.students_data = [
                {
                    "student_id":      s["student_id"],
                    "Name":            s["name"],
                    "Total Classes":   s["total_classes"],
                    "Attended Classes": s["attended_classes"],
                    "Attendance %":    s["attendance_percentage"],
                    "Performance Score": s["performance_score"],
                    "Score History":   s["score_history"],
                }
                for s in raw
            ]
    return st.session_state.students_data or []

def _get_timetable() -> dict:
    if st.session_state.timetable_data is None:
        st.session_state.timetable_data = api_get("/faculty/me/timetable") or {}
    return st.session_state.timetable_data

# ─────────────────────────────────────────────
# MODULE A – ATTENDANCE DASHBOARD
# ─────────────────────────────────────────────
def render_attendance_dashboard():
    st.markdown('<p class="section-title">📋 Attendance Dashboard</p>', unsafe_allow_html=True)
    students = _get_students()
    if not students:
        return

    df = pd.DataFrame([{k: v for k, v in s.items() if k != "Score History"} for s in students])

    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total Students", len(df))
    c2.metric("📊 Avg Attendance", f"{df['Attendance %'].mean():.1f}%")
    c3.metric("⚠️ At-Risk (<75%)", len(df[df["Attendance %"] < 75]))

    st.dataframe(
        df.drop(columns=["student_id"]).style.map(
            lambda x: "color: #f85149" if isinstance(x, float) and x < 75 else "",
            subset=["Attendance %"],
        ),
        use_container_width=True,
    )
    if st.button("🔄 Refresh"):
        st.session_state.students_data = None
        st.rerun()

# ─────────────────────────────────────────────
# MODULE B – PERFORMANCE TRACKER
# ─────────────────────────────────────────────
def render_student_performance():
    st.markdown('<p class="section-title">📈 Student Performance Tracker</p>', unsafe_allow_html=True)
    students = _get_students()
    if not students:
        return

    names = [s["Name"] for s in students]
    chosen = st.selectbox("Select Student", names, key="perf_select")
    student = next(s for s in students if s["Name"] == chosen)

    k1, k2 = st.columns(2)
    k1.metric("🎯 Current Grade Avg", f"{student['Performance Score']}/100")
    k2.metric("📝 Exams Taken", len(student["Score History"]))

    st.line_chart(pd.DataFrame({"Score": student["Score History"]}))

# ─────────────────────────────────────────────
# MODULE C – MARKS ENTRY
# ─────────────────────────────────────────────
def render_marks_entry():
    st.markdown('<p class="section-title">📝 Marks Entry Portal</p>', unsafe_allow_html=True)
    students = _get_students()
    if not students:
        return

    exam_type = st.selectbox("Assessment Type", ["Quiz", "Midterm", "End-term", "Assignment"])
    st.info("Enter scores below and click Submit — changes are recorded with an audit trail.")

    with st.form("marks_entry_form"):
        col_n, col_l, col_i = st.columns([2, 1, 1])
        col_n.markdown("**Student Name**")
        col_l.markdown("**Last Score**")
        col_i.markdown("**New Score**")

        new_entries = {}
        for i, student in enumerate(students):
            c_name, c_last, c_input = st.columns([2, 1, 1])
            c_name.write(student["Name"])
            c_last.write(student["Score History"][-1] if student["Score History"] else "N/A")
            new_entries[student["student_id"]] = c_input.number_input(
                f"Score for {student['Name']}", 0.0, 100.0, step=1.0,
                label_visibility="collapsed", key=f"score_{i}",
            )

        if st.form_submit_button("🚀 Submit & Update Records"):
            payload = {
                "assessment_type": exam_type,
                "course_id": 1,
                "marks": [{"student_id": sid, "score": score} for sid, score in new_entries.items()],
            }
            result = api_post("/assessments/marks/bulk", payload)
            if result:
                st.success(result.get("message", "Marks submitted!"))
                st.balloons()
                st.session_state.students_data = None

# ─────────────────────────────────────────────
# MODULE D – TIMETABLE  (proper visual grid)
# ─────────────────────────────────────────────
def render_timetable():
    st.markdown('<p class="section-title">📅 Weekly Timetable</p>', unsafe_allow_html=True)

    tt = _get_timetable()
    if not tt:
        st.warning("No timetable data available.")
        return

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    SLOTS = [
        "09:00-10:00", "10:00-11:00", "11:00-12:00",
        "12:00-13:00", "14:00-15:00", "15:00-16:00", "16:00-17:00",
    ]

    # Build HTML table
    header = "<tr><th>Time</th>" + "".join(f"<th>{d}</th>" for d in DAYS) + "</tr>"

    rows_html = ""
    for slot in SLOTS:
        cells = f'<td class="time-col">{slot}</td>'
        for day in DAYS:
            cell = tt.get(day, {}).get(slot)
            if cell:
                cells += (
                    f'<td class="has-class">'
                    f'<span class="class-pill">{cell["course"]}'
                    f'<span class="room-tag">📍 {cell["room"]}</span>'
                    f'</span></td>'
                )
            else:
                cells += "<td>—</td>"
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(
        f'<div class="tt-wrap"><table class="tt"><thead>{header}</thead><tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )

    if st.button("🔄 Refresh Timetable"):
        st.session_state.timetable_data = None
        st.rerun()

# ─────────────────────────────────────────────
# MODULE E – MANAGE RECORDS
# ─────────────────────────────────────────────
def render_manage_records():
    st.markdown('<p class="section-title">⚙️ Manage Records</p>', unsafe_allow_html=True)
    with st.form("reg_form"):
        name  = st.text_input("Full Name")
        total = st.number_input("Total Classes", 1, 100, 40)
        if st.form_submit_button("➕ Register Student"):
            if name:
                result = api_post("/students", {"name": name, "total_classes": int(total)})
                if result:
                    st.success(f"Registered {name}!")
                    st.session_state.students_data = None
            else:
                st.warning("Please enter a name.")

# ─────────────────────────────────────────────
# PROFILE DROPDOWN
# ─────────────────────────────────────────────
def render_profile_dropdown():
    if not st.session_state.profile_open:
        return
    fac = _get_faculty()
    name  = fac.get("name",       "Dr. Smith")
    dept  = fac.get("dept",       "Computer Science")
    fid   = fac.get("fac_id", fac.get("faculty_id", "FAC-CS-2024"))
    email = fac.get("email",      "dr.smith@university.edu")
    phone = fac.get("phone",      "+91 98765 43210")

    st.markdown(f"""
    <div class="profile-dropdown">
        <div class="pd-header">
            <span class="pd-header-name">{name}</span>
            <span class="pd-header-role">{dept}</span>
        </div>
        <div class="pd-divider"></div>
        <div class="pd-body">
            <div class="pd-row"><span class="pd-icon">🎓</span><span class="pd-value">Faculty ID: {fid}</span></div>
            <div class="pd-row"><span class="pd-icon">✉️</span><span class="pd-value">{email}</span></div>
            <div class="pd-row"><span class="pd-icon">📱</span><span class="pd-value">{phone}</span></div>
        </div>
        <div class="pd-divider"></div>
        <div class="pd-manage"><span>⚙️</span><span class="pd-manage-text">Manage Account</span></div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    _ensure_state()
    _check_auth()          # ← blocks here if not logged in
    fac = _get_faculty()

    # Avatar button top-right
    _, col_btn = st.columns([11, 1])
    with col_btn:
        initials = "".join(w[0].upper() for w in fac.get("name", "Dr Smith").split() if w[0].isalpha())[:2]
        if st.button(initials, key="prof_btn", help="View profile"):
            st.session_state.profile_open = not st.session_state.profile_open

    render_profile_dropdown()

    st.markdown(
        "<h1 style='text-align:center; margin-top:-1.5rem;'>🎓 Faculty Dashboard</h1>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### 🎓 Navigation")
        page = st.radio(
            "Go to:",
            ["📋  Attendance", "📈  Performance", "📝  Marks Entry", "📅  Timetable", "⚙️  Manage Records"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(f"👤 **{fac.get('name', 'Dr. Smith')}**")
        st.markdown(f"📆 {datetime.now().strftime('%d %b %Y')}")
        st.markdown("---")
        st.caption(f"🔗 `{API_BASE_URL}`")
        if st.button("🚪 Logout", use_container_width=True):
            for key in ["authenticated", "auth_token", "auth_username",
                        "auth_role", "fac_profile", "students_data", "timetable_data"]:
                st.session_state[key] = None if "data" in key or "profile" in key else ""
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="page-wrapper">', unsafe_allow_html=True)
    if   "Attendance"     in page: render_attendance_dashboard()
    elif "Performance"    in page: render_student_performance()
    elif "Marks Entry"    in page: render_marks_entry()
    elif "Timetable"      in page: render_timetable()
    elif "Manage Records" in page: render_manage_records()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
