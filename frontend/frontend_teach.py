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
        st.error("❌ Backend Offline")
        return None

def api_post(path: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        st.error("❌ Backend Offline")
        return None

# ─────────────────────────────────────────────
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="Faculty Dashboard", page_icon="🎓", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif; }
.stApp { background: #0d1117; color: #c9d1d9; }

/* Profile dropdown styling */
.profile-dropdown {
    position: fixed; top: 70px; right: 20px; z-index: 1000;
    background: #1a1f2e; border: 1px solid #2d3448; border-radius: 16px;
    width: 280px; padding: 20px; box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    animation: dropIn 0.2s ease-out;
}
@keyframes dropIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
.pd-name { font-size: 1.2rem; font-weight: 700; color: #fff; margin-bottom: 2px; display:block; }
.pd-dept { font-size: 0.75rem; color: #3b9eff; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 15px; display:block; }
.pd-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; color: #a8b3c8; font-size: 0.9rem; }
.pd-manage { margin-top: 15px; padding-top: 15px; border-top: 1px solid #2d3448; color: #fff; font-weight: 600; text-align: center; cursor: pointer; }

/* Avatar button styling */
div[data-testid="stColumn"]:last-child button {
    width: 46px !important; height: 46px !important; border-radius: 50% !important;
    background: linear-gradient(135deg, #1a6ed8, #3b9eff) !important;
    color: #fff !important; border: none !important; font-weight: 700 !important;
}

div[data-testid="stForm"] { background: #161b27; border: 1px solid #21262d; border-radius: 12px; }
.section-title { font-size: 1.4rem; color: #e6edf3; border-left: 3px solid #238636; padding-left: 12px; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STATE & FETCHING
# ─────────────────────────────────────────────
def _ensure_state():
    if "profile_open" not in st.session_state: st.session_state.profile_open = False
    if "students_data" not in st.session_state: st.session_state.students_data = None
    if "fac_profile" not in st.session_state: st.session_state.fac_profile = None

def _get_faculty():
    if st.session_state.fac_profile is None:
        st.session_state.fac_profile = api_get("/faculty/me")
    return st.session_state.fac_profile

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

# ─────────────────────────────────────────────
# MODULES
# ─────────────────────────────────────────────
def render_profile_dropdown():
    fac = _get_faculty()
    if fac and st.session_state.profile_open:
        st.markdown(f"""
        <div class="profile-dropdown">
            <span class="pd-name">{fac['name']}</span>
            <span class="pd-dept">{fac['dept']}</span>
            <div class="pd-row"><span>🎓</span><span>ID: {fac['fac_id']}</span></div>
            <div class="pd-row"><span>✉️</span><span>{fac['email']}</span></div>
            <div class="pd-row"><span>📱</span><span>{fac['phone']}</span></div>
            <div class="pd-manage">⚙️ Manage Account</div>
        </div>
        """, unsafe_allow_html=True)

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

def render_timetable():
    st.markdown('<p class="section-title">📅 Weekly Schedule</p>', unsafe_allow_html=True)
    tt = api_get("/faculty/me/timetable")
    if tt:
        slots = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "14:00-15:00"]
        rows = []
        for slot in slots:
            row = {"Time": slot}
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
                cell = tt.get(day, {}).get(slot)
                row[day] = f"{cell['course']} ({cell['room']})" if cell else "—"
            rows.append(row)
        st.table(pd.DataFrame(rows).set_index("Time"))

def main():
    _ensure_state()
    fac = _get_faculty()
    
    # Header logic for profile icon
    col_title, col_icon = st.columns([10, 1])
    with col_icon:
        # Generate initials e.g. "Dr. Smith" -> "DS"
        initials = "".join([n[0] for n in fac['name'].split() if n[0].isalpha()]) if fac else "SA"
        if st.button(initials, key="prof_btn"):
            st.session_state.profile_open = not st.session_state.profile_open
            
    render_profile_dropdown()

    st.sidebar.markdown("### 🎓 Navigation")
    page = st.sidebar.radio("Go to:", ["📋 Attendance", "📈 Performance", "📝 Marks Entry", "📅 Timetable", "⚙️ Manage Records"], label_visibility="collapsed")
    
    if "Attendance" in page: render_attendance_dashboard()
    elif "Timetable" in page: render_timetable()
    elif "Manage Records" in page:
        st.markdown('<p class="section-title">⚙️ Manage Records</p>', unsafe_allow_html=True)
        with st.form("reg_form"):
            name = st.text_input("Full Name")
            total = st.number_input("Total Classes", 1, 100, 40)
            if st.form_submit_button("➕ Register"):
                if name and api_post("/students", {"name": name, "total_classes": int(total)}):
                    st.success(f"Registered {name}!"); st.session_state.students_data = None
    else:
        st.info("Module content loading...")

if __name__ == "__main__":
    main()