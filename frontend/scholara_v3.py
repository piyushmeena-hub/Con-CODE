"""
╔══════════════════════════════════════════════════════════════════════╗
║         SCHOLARA v3 — Location + Photo Proof Attendance              ║
║         Subject-wise · Day-wise · GPS verified · Camera proof        ║
╚══════════════════════════════════════════════════════════════════════╝

New in v3 (Strict Mode):
  • Mark attendance STRICTLY requires live device GPS + Photo Proof
  • Bulk "Attended" and quick-mark bypasses have been removed
  • Enlarged, clean UI navigation in the sidebar
  • Expandable proof viewer per subject per day

Run:
    pip install streamlit streamlit-javascript requests pillow
    streamlit run scholara_v3.py
"""

import streamlit as st
import streamlit.components.v1 as components
import time
import random
import calendar
import base64
import json
import requests
from datetime import date, timedelta, datetime
from typing import Generator
from io import BytesIO

def add_task():
    task_text = st.session_state.new_task_input.strip()
    if task_text:
        new_id = str(time.time())
        new_task = {"id": new_id, "text": task_text, "completed": False}
        st.session_state.tasks.insert(0, new_task)
        # Send to database
        requests.post("http://localhost:8000/api/v1/productivity/tasks", json=new_task)
        st.session_state.new_task_input = ""

def toggle_task(task_id):
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            t["completed"] = not t["completed"]
            # Tell database to toggle
            requests.put(f"http://localhost:8000/api/v1/productivity/tasks/{task_id}")
            break

def delete_task(task_id):
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
    # Tell database to delete
    requests.delete(f"http://localhost:8000/api/v1/productivity/tasks/{task_id}")
# ══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════

# THRESHOLD is now purely dynamic via st.session_state
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

ATT  = "att"
MISS = "miss"
OFF  = "off"
CLEAR = None

STATUS_LABELS = {ATT: "✅ Attended", MISS: "❌ Missed", OFF: "— Holiday", CLEAR: "○ Not marked"}
STATUS_COLORS = {ATT: "#22c55e", MISS: "#ef4444", OFF: "#f59e0b", CLEAR: "#6b7280"}

DEFAULT_SUBJECTS = [
    "Mechanical", "Maths", "Physics", "English Lecture",
    "Economics", "EDC", "Signal & System",
    "AUTO CAD LAB", "Mechanical LAB", "Physics LAB",
    "English LAB", "EDC LAB", "Signal LAB", "Phy TUT", "Maths TUT",
]

DEFAULT_TIMETABLE = {
    "Monday":    ["Mechanical", "Maths TUT", "Physics LAB", "EDC", "EDC LAB", "Maths"],
    "Tuesday":   ["AUTO CAD LAB", "Physics", "English Lecture", "EDC", "Signal & System"],
    "Wednesday": ["Maths", "Mechanical", "English Lecture", "Signal & System"],
    "Thursday":  ["Mechanical LAB", "Physics", "Economics", "EDC"],
    "Friday":    ["Maths", "Economics", "English Lecture", "Phy TUT", "Signal & System", "Signal LAB"],
    "Saturday":  [],
    "Sunday":    [],
}

MOCK_SNIPPETS = [
    {"page": 4,  "snippet": "This concept is foundational. Mastering it will help with all related numerical and theory questions in exams."},
    {"page": 11, "snippet": "First formalized in the 19th century, this principle remains central to modern engineering and science curricula."},
    {"page": 17, "snippet": "Key formula: the relationship between these variables follows a linear proportion under standard conditions (Chapter 3)."},
    {"page": 23, "snippet": "Application: widely used in circuit analysis, structural mechanics, and thermodynamics — all high-weight exam topics."},
]

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════

def init_state():
    if "subjects" not in st.session_state:
        st.session_state.subjects = list(DEFAULT_SUBJECTS)
    if "timetable" not in st.session_state:
        import copy
        st.session_state.timetable = copy.deepcopy(DEFAULT_TIMETABLE)
    # attendance_log: {date_str: {subject: {"status": str, "proof": dict|None}}}
    if "attendance_log" not in st.session_state:
        st.session_state.attendance_log = {}
        # Fetch historical data from FastAPI on startup
        try:
            res = requests.get("http://localhost:8000/api/v1/attendance/")
            if res.status_code == 200:
                api_records = res.json()
                for r in api_records:
                    date_str = r["date"]
                    subj = r["subject"]
                    
                    # Ensure the date exists in our dictionary
                    if date_str not in st.session_state.attendance_log:
                        st.session_state.attendance_log[date_str] = {}
                        
                    # Reconstruct the proof dictionary if it exists
                    proof_data = None
                    if r.get("proof"):
                        proof_data = {
                            "timestamp": r["proof"]["timestamp"].replace("T", " ")[:16],
                            "lat": r["proof"]["latitude"],
                            "lon": r["proof"]["longitude"],
                            "accuracy": r["proof"]["accuracy"],
                            "address": r["proof"]["address"],
                            "photo_url": r["proof"]["photo_url"],
                        }
                        
                    # Inject it into Streamlit's memory
                    st.session_state.attendance_log[date_str][subj] = {
                        "status": r["status"],
                        "proof": proof_data
                    }
        except Exception as e:
            print(f"Backend offline or unreachable. Starting with empty logs. Error: {e}")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "source_snippets" not in st.session_state:
        st.session_state.source_snippets = []
    if "uploaded_doc" not in st.session_state:
        st.session_state.uploaded_doc = {"loaded": False, "filename": None}
    if "viewed_date" not in st.session_state:
        st.session_state.viewed_date = date.today()
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = date.today().year
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = date.today().month
    if "pending_proof" not in st.session_state:
        st.session_state.pending_proof = None
    if "captured_location" not in st.session_state:
        st.session_state.captured_location = None
    if "active_page" not in st.session_state:
        st.session_state.active_page = "🧭 Day View"
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "target_attendance" not in st.session_state:
        st.session_state.target_attendance = 75.0
    if "has_warning_email_been_sent" not in st.session_state:
        st.session_state.has_warning_email_been_sent = False
# ══════════════════════════════════════════════════════════════════════
# TODO LOGIC HANDLERS
# ══════════════════════════════════════════════════════════════════════

def add_task():
    task_text = st.session_state.new_task_input.strip()
    if task_text:
        new_id = str(time.time())
        st.session_state.tasks.insert(0, {"id": new_id, "text": task_text, "completed": False})
        st.session_state.new_task_input = ""

def toggle_task(task_id):
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            t["completed"] = not t["completed"]
            break

def delete_task(task_id):
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def get_day_name(d: date) -> str:
    return DAYS[d.weekday()]

def subjects_on_day(d: date) -> list:
    return st.session_state.timetable.get(get_day_name(d), [])

def get_record(d: date, subject: str) -> dict:
    key = d.isoformat()
    rec = st.session_state.attendance_log.get(key, {}).get(subject, None)
    if rec is None:
        return {"status": CLEAR, "proof": None}
    return rec

def get_status(d: date, subject: str):
    return get_record(d, subject)["status"]

def set_record(d: date, subject: str, status, proof=None):
    key = d.isoformat()
    if key not in st.session_state.attendance_log:
        st.session_state.attendance_log[key] = {}
    existing_proof = st.session_state.attendance_log[key].get(subject, {}).get("proof", None)
    st.session_state.attendance_log[key][subject] = {
        "status": status,
        "proof": proof if proof is not None else existing_proof,
    }

def subject_stats(subject: str) -> dict:
    total = attended = missed = off_count = 0
    for day_data in st.session_state.attendance_log.values():
        rec = day_data.get(subject, None)
        if rec is None:
            continue
        s = rec.get("status", CLEAR) if isinstance(rec, dict) else rec
        if s == ATT:
            total += 1; attended += 1
        elif s == MISS:
            total += 1; missed += 1
        elif s == OFF:
            off_count += 1

    pct = round(attended / total * 100, 2) if total > 0 else 0.0
    can_miss = 0
    need = 0
    t = st.session_state.target_attendance
    if total > 0:
        if pct >= t:
            can_miss = int((attended - t / 100 * total) / (1 - t / 100))
        else:
            num = (t / 100) * total - attended
            den = 1 - t / 100
            need = max(0, int(num / den) + (1 if den and (num / den) % 1 > 0 else 0))
    return {"total": total, "attended": attended, "missed": missed,
            "off": off_count, "pct": pct, "can_miss": can_miss, "need": need}

def overall_stats() -> dict:
    total = attended = missed = off_count = 0
    for subject in st.session_state.subjects:
        s = subject_stats(subject)
        total += s["total"]; attended += s["attended"]
        missed += s["missed"]; off_count += s["off"]
    pct = round(attended / total * 100, 2) if total > 0 else 0.0
    return {"total": total, "attended": attended, "missed": missed, "off": off_count, "pct": pct}

def day_dot_color(d: date) -> str:
    subjects = subjects_on_day(d)
    if not subjects:
        return "#374151"
    statuses = [get_status(d, s) for s in subjects]
    marked = [s for s in statuses if s is not None]
    if not marked: return "#6b7280"
    if all(s == OFF for s in marked): return "#f59e0b"
    if all(s == ATT for s in marked): return "#22c55e"
    if all(s == MISS for s in marked): return "#ef4444"
    if any(s is not None for s in marked): return "#8b5cf6"
    return "#6b7280"

def reverse_geocode(lat: float, lon: float) -> str:
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "Scholara-Attendance-App/3.0"},
            timeout=5,
        )
        data = r.json()
        addr = data.get("address", {})
        parts = [
            addr.get("road") or addr.get("pedestrian") or addr.get("building"),
            addr.get("suburb") or addr.get("neighbourhood") or addr.get("village"),
            addr.get("city") or addr.get("town") or addr.get("county"),
            addr.get("state"),
        ]
        return ", ".join(p for p in parts if p) or data.get("display_name", "Unknown location")
    except Exception:
        return "Location resolved (offline mode)"

def img_to_b64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode()

# ══════════════════════════════════════════════════════════════════════
# LOCATION + PHOTO PROOF COMPONENT
# ══════════════════════════════════════════════════════════════════════

STUDY_TRACKER_HTML = """
<div class="dashboard">
    <div class="panel clock-panel">
        <div class="panel-header">Live Session Clock</div>
        
        <div style="margin-bottom: 24px;">
            <input type="text" id="subject-input" placeholder="What are you focusing on? (e.g. Mathematics)" 
                   style="width:100%;background:#121212;border:1px solid #374151;color:#F3F4F6;padding:14px;border-radius:8px;font-size:0.95rem;outline:none;" />
        </div>
        
        <div class="clock-container">
            <svg viewBox="0 0 220 220" width="220" height="220">
                <g id="ticks"></g>
                <circle cx="110" cy="110" r="95" fill="none" stroke="#374151" stroke-width="8"></circle>
                <circle id="progress-circle" cx="110" cy="110" r="95" fill="none" stroke="#06b6d4" stroke-width="8"
                        stroke-dasharray="596.9" stroke-dashoffset="596.9" stroke-linecap="round" 
                        transform="rotate(-90 110 110)"></circle>
                <line id="sweeping-hand" x1="110" y1="110" x2="110" y2="25" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"></line>
            </svg>
            <div id="clock-text">00:00:00</div>
        </div>
        <div class="controls">
            <button id="pause-btn" style="background:#f59e0b;">Start Session</button>
            <button id="stop-btn" style="background:#ef4444;">Stop</button>
        </div>
    </div>
    
    <div class="panel history-panel">
        <div class="panel-header">Completed Session Log</div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Subject</th>
                        <th>Start</th>
                        <th>End</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody id="history-list">
                    </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    .dashboard {
        display: grid;
        grid-template-columns: 350px 1fr;
        gap: 20px;
        font-family: 'IBM Plex Sans', sans-serif;
        color: #F3F4F6;
    }
    .panel {
        background: #1E1E1E;
        border: 1px solid #374151;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        padding: 24px;
        display: flex;
        flex-direction: column;
    }
    .panel-header {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 24px;
        color: #F3F4F6;
    }
    .clock-container {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 28px;
    }
    #clock-text {
        position: absolute;
        font-size: 1.9rem;
        font-weight: 700;
        color: #F3F4F6;
        font-variant-numeric: tabular-nums;
        letter-spacing: 1px;
    }
    /* Smooth Continuous Sweep Animation */
    #sweeping-hand {
        transition: transform 1s linear;
    }
    #progress-circle {
        transition: stroke-dashoffset 1s linear;
    }
    .controls {
        display: flex;
        gap: 12px;
    }
    .controls button {
        flex: 1;
        border: none;
        border-radius: 8px;
        padding: 12px;
        color: white;
        font-weight: 700;
        font-size: 0.95rem;
        cursor: pointer;
        transition: filter 0.2s, transform 0.1s;
    }
    .controls button:hover {
        filter: brightness(1.1);
        transform: translateY(-1px);
    }
    .controls button:active {
        transform: translateY(1px);
    }
    
    .table-container {
        overflow-y: auto;
        flex: 1;
        max-height: 400px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        font-size: 0.9rem;
    }
    th {
        color: #9CA3AF;
        font-weight: 600;
        padding-bottom: 12px;
        border-bottom: 1px solid #374151;
    }
    td {
        padding: 14px 0;
        border-bottom: 1px solid #374151;
        color: #E5E7EB;
    }
    tr:hover td {
        color: #F3F4F6;
        background: rgba(255,255,255,0.02);
    }
    .subject-badge {
        background: #2563eb;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; border-radius: 4px; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #4B5563; }
</style>

<script>
    const ticksGroup = document.getElementById('ticks');
    for (let i = 0; i < 60; i++) {
        const angle = (i * 6 * Math.PI) / 180;
        const isHour = i % 5 === 0;
        const r1 = isHour ? 82 : 88;
        const r2 = 91;
        const x1 = 110 + r1 * Math.sin(angle);
        const y1 = 110 - r1 * Math.cos(angle);
        const x2 = 110 + r2 * Math.sin(angle);
        const y2 = 110 - r2 * Math.cos(angle);
        
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', isHour ? '#9CA3AF' : '#4B5563');
        line.setAttribute('stroke-width', isHour ? '2' : '1');
        ticksGroup.appendChild(line);
    }
    
    let isRunning = false;
    let currentSessionTime = 0;
    let timer = null;
    let startTimestamp = null;
    let sessions = JSON.parse(localStorage.getItem('scholara_history_v2')) || [];
    
    let legacyS = JSON.parse(localStorage.getItem('scholara_history'));
    if (legacyS && sessions.length === 0) {
        sessions = legacyS.map(s => ({ ...s, subject: s.subject || 'General Focus' }));
        localStorage.setItem('scholara_history_v2', JSON.stringify(sessions));
        localStorage.removeItem('scholara_history');
    }
    
    const clockText = document.getElementById('clock-text');
    const sweepHand = document.getElementById('sweeping-hand');
    const progressArc = document.getElementById('progress-circle');
    const historyList = document.getElementById('history-list');
    const pauseBtn = document.getElementById('pause-btn');
    const stopBtn = document.getElementById('stop-btn');
    const subInput = document.getElementById('subject-input');
    
    function formatTime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        const pad = n => n.toString().padStart(2, '0');
        return `${pad(h)}:${pad(m)}:${pad(s)}`;
    }
    
    function formatDuration(seconds) {
        if (seconds < 60) return `${seconds}s`;
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        if (h > 0) return `${h}h ${padM(m)}m`;
        return `${m}m`;
    }
    function padM(n) { return n.toString().padStart(2, '0'); }
    
    function renderHistory() {
        historyList.innerHTML = '';
        if (sessions.length === 0) {
            historyList.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#6B7280; padding: 40px;">No study sessions tracked yet. Enter a subject and hit Start!</td></tr>';
            return;
        }
        
        [...sessions].reverse().slice(0, 10).forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.date}</td>
                <td><span class="subject-badge">${s.subject || '—'}</span></td>
                <td>${s.start}</td>
                <td>${s.end}</td>
                <td><strong>${s.duration}</strong></td>
            `;
            historyList.appendChild(tr);
        });
    }
    
    function updateVisuals() {
        clockText.innerText = formatTime(currentSessionTime);
        
        let deg = currentSessionTime * 6; 
        sweepHand.setAttribute('transform', `rotate(${deg} 110 110)`);
        
        let fraction = (currentSessionTime % 3600) / 3600;
        let offset = 596.90 - (fraction * 596.90);
        progressArc.setAttribute('stroke-dashoffset', offset);
    }
    
    function startTimer() {
        if (!isRunning) {
            if (currentSessionTime === 0) startTimestamp = new Date();
            isRunning = true;
            pauseBtn.innerText = 'Pause';
            pauseBtn.style.background = '#f59e0b';
            subInput.disabled = true;
            timer = setInterval(() => { currentSessionTime++; updateVisuals(); }, 1000);
        } else {
            isRunning = false;
            clearInterval(timer);
            pauseBtn.innerText = 'Resume';
            pauseBtn.style.background = '#2563eb';
        }
    }
    
    function stopTimer() {
        if (currentSessionTime === 0 && !isRunning) return; 
        
        isRunning = false;
        clearInterval(timer);
        
        const endDate = new Date();
        const startStr = startTimestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const endStr = endDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const dateTokens = endDate.toDateString().split(' ');
        const dateStr = `${dateTokens[2]} ${dateTokens[1]}`;
        const subjStr = subInput.value.trim() || 'General Focus';
        
        sessions.push({ date: dateStr, subject: subjStr, start: startStr, end: endStr, duration: formatDuration(currentSessionTime) });
        localStorage.setItem('scholara_history_v2', JSON.stringify(sessions));
        
        // --- NEW: SEND TO BACKEND ---
        fetch('http://localhost:8000/api/v1/productivity/session', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                date: dateStr,
                subject: subjStr,
                start_time: startStr,
                end_time: endStr,
                duration: formatDuration(currentSessionTime)
            })
        });
        // ----------------------------
        
        currentSessionTime = 0;
        startTimestamp = null;
        subInput.disabled = false;
        subInput.value = '';
        pauseBtn.innerText = 'Start Session';
        pauseBtn.style.background = '#2563eb';
        
        sweepHand.style.transition = 'none';
        progressArc.style.transition = 'none';
        updateVisuals();
        
        setTimeout(() => {
            sweepHand.style.transition = 'transform 1s linear';
            progressArc.style.transition = 'stroke-dashoffset 1s linear';
        }, 50);
        
        renderHistory();
    }
    
    pauseBtn.addEventListener('click', startTimer);
    stopBtn.addEventListener('click', stopTimer);
    
    updateVisuals();
    renderHistory();
</script>
"""

def render_study_tracker():
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    import streamlit.components.v1 as components
    components.html(STUDY_TRACKER_HTML, height=600)

def render_todo_widget():
    st.markdown("""
        <style>
        .todo-header { font-size:1.15rem; font-weight:700; color:#F3F4F6; margin-bottom:16px; margin-top:0px; display:flex; align-items:center; gap:8px; }
        .task-empty { text-align:center; color:#6B7280; font-size:0.9rem; padding: 30px 10px; }
        .task-text { color: #E5E7EB; font-size: 0.95rem; margin-top: 4px; }
        .task-text.completed { text-decoration: line-through; color: #6B7280; }
        /* Target generic input fields explicitly */
        div[data-testid="stTextInput"] input { padding: 12px 14px!important; font-size: 0.9rem!important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 class='todo-header'>📋 To-Do List</h3>", unsafe_allow_html=True)
    
    # Input Layout
    c1, c2 = st.columns([7, 3])
    with c1:
        st.text_input("New Task", key="new_task_input", label_visibility="collapsed", placeholder="What needs to be done?", on_change=add_task)
    with c2:
        st.button("Add", on_click=add_task, use_container_width=True, type="primary")
        
    st.markdown("<hr style='margin: 10px 0; border-color: #374151;'>", unsafe_allow_html=True)
    
    # Task List
    if not st.session_state.tasks:
        st.markdown("<div class='task-empty'>✅ All caught up! Add a new goal to begin.</div>", unsafe_allow_html=True)
    else:
        for task in st.session_state.tasks:
            tcols = st.columns([1, 8, 2], vertical_alignment="center")
            with tcols[0]:
                st.checkbox("", value=task["completed"], key=f"chk_{task['id']}", on_change=toggle_task, args=(task["id"],), label_visibility="collapsed")
            with tcols[1]:
                cls = "task-text completed" if task["completed"] else "task-text"
                st.markdown(f"<div class='{cls}'>{task['text']}</div>", unsafe_allow_html=True)
            with tcols[2]:
                st.button("🗑️", key=f"del_{task['id']}", on_click=delete_task, args=(task["id"],), use_container_width=True)

def page_focus_time():
    st.markdown("""<h2 style='font-family:Georgia,serif;color:#F3F4F6;margin-bottom:.5rem;'>
        🎯 Focus Time</h2>
        <p style='color:#9CA3AF;font-size:.9rem;margin-top:0;'>
        A distraction-free environment to log deep work sessions.</p>
    """, unsafe_allow_html=True)
    st.divider()
    
    # Grid Layout: 2/3 Clock, 1/3 Task Manager
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        render_study_tracker()
        
    with right_col:
        render_todo_widget()


LOCATION_JS = """
<div id="loc-status" style="font-family:monospace;font-size:13px;color:#9CA3AF;
     padding:8px 0;">Requesting location…</div>
<script>
(function() {
    var status = document.getElementById('loc-status');
    if (!navigator.geolocation) {
        status.textContent = 'ERROR: Geolocation not supported by this browser.';
        status.style.color = '#ef4444';
        return;
    }
    navigator.geolocation.getCurrentPosition(
        function(pos) {
            var lat = pos.coords.latitude.toFixed(6);
            var lon = pos.coords.longitude.toFixed(6);
            var acc = Math.round(pos.coords.accuracy);
            status.innerHTML =
                '<span style="color:#22c55e;">&#10003; Location captured</span><br>' +
                '<span style="color:#9CA3AF;font-size:12px;">Lat: ' + lat +
                ' &nbsp; Lon: ' + lon + ' &nbsp; ±' + acc + 'm</span>';
            var msg = JSON.stringify({lat: parseFloat(lat), lon: parseFloat(lon), acc: acc});
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: msg}, '*');
        },
        function(err) {
            var msgs = {1:'Permission denied', 2:'Position unavailable', 3:'Timeout'};
            status.innerHTML =
                '<span style="color:#ef4444;">&#10007; ' + (msgs[err.code]||'Unknown error') + '</span><br>' +
                '<span style="color:#9CA3AF;font-size:12px;">Please allow location access and retry.</span>';
        },
        {enableHighAccuracy: true, timeout: 10000, maximumAge: 0}
    );
})();
</script>
"""

def render_proof_card(proof: dict, subject: str):
    if not proof:
        return

    ts = proof.get("timestamp", "")
    lat = proof.get("lat")
    lon = proof.get("lon")
    address = proof.get("address", "")
    photo_url = proof.get("photo_url") # Fetching the URL instead of base64
    acc = proof.get("accuracy", "")

    with st.container():
        st.markdown(
            f"""
            <div style='background:#1E1E1E;border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);border-radius:14px;
                        padding:14px 16px;margin-top:6px;'>
                <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px;'>
                    <span style='font-size:14px;'>📍</span>
                    <span style='color:#0284c7;font-weight:600;font-size:.85rem;'>
                        Attendance Proof — {subject}
                    </span>
                    <span style='margin-left:auto;background:#dcfce7;color:#166534;
                                 font-size:.7rem;padding:2px 8px;border-radius:20px;
                                 font-weight:600;'>✓ VERIFIED</span>
                </div>
                <div style='display:grid;grid-template-columns:auto 1fr;
                            gap:6px 12px;font-size:.78rem;'>
                    <span style='color:#9CA3AF;'>🕐 Time</span>
                    <span style='color:#E5E7EB;'>{ts}</span>
                    <span style='color:#9CA3AF;'>📌 Coords</span>
                    <span style='color:#E5E7EB;'>
                        {f"{lat:.6f}, {lon:.6f}" if lat else "Not captured"}
                        {f" (±{acc}m)" if acc else ""}
                    </span>
                    <span style='color:#9CA3AF;'>🏛️ Location</span>
                    <span style='color:#E5E7EB;'>{address or "Resolving…"}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if photo_url:
            st.markdown(
                f"""
                <div style='margin-top:10px;border-radius:10px;overflow:hidden;
                            border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);'>
                    <img src='{photo_url}'
                         style='width:100%;max-height:200px;object-fit:cover;display:block;'/>
                    <div style='background:#1E1E1E;padding:4px 10px;
                                font-size:.7rem;color:#9CA3AF;text-align:right;'>
                        Photo proof captured at {ts}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )



# ══════════════════════════════════════════════════════════════════════
# VERIFIED MARK ATTENDANCE DIALOG (STRICT MODE)
# ══════════════════════════════════════════════════════════════════════

def render_verified_mark_section(d: date, subject: str):
    current_proof = get_record(d, subject).get("proof")
    current_status = get_status(d, subject)

    with st.expander(
        f"{'🔒' if current_status == ATT and current_proof else '📍'} "
        f"{'View Proof' if current_status == ATT and current_proof else 'Mark with Proof'}",
        expanded=False,
    ):
        if current_status == ATT and current_proof:
            render_proof_card(current_proof, subject)
            if st.button("🔄 Re-capture Proof", key=f"recapture_{d}_{subject}", use_container_width=True):
                set_record(d, subject, CLEAR, None) # Clear it completely to force proper remarking
                st.rerun()
            return

        st.markdown(
            "<p style='color:#9CA3AF;font-size:.82rem;margin-bottom:12px;'>"
            "To mark <b>Attended with proof</b>, you must provide your location and a photo.</p>",
            unsafe_allow_html=True,
        )

        # ── Step 1: Location ─────────────────────────────────────────
        st.markdown("**Step 1 — Capture your location**")

        loc_key = f"loc_{d}_{subject}"
        stored_loc_key = f"loc_stored_{d}_{subject}"

        loc_result = components.html(LOCATION_JS, height=60)

        with st.expander("📍 Enter coordinates manually (if browser blocks location)", expanded=False):
            ml1, ml2 = st.columns(2)
            man_lat = ml1.number_input("Latitude", value=26.9124, format="%.6f", key=f"mlat_{d}_{subject}")
            man_lon = ml2.number_input("Longitude", value=75.7873, format="%.6f", key=f"mlon_{d}_{subject}")
            man_acc = st.number_input("Accuracy (meters)", value=50, min_value=1, max_value=10000, key=f"macc_{d}_{subject}")
            if st.button("📍 Use These Coordinates", key=f"use_manual_{d}_{subject}", use_container_width=True):
                with st.spinner("Resolving address…"):
                    address = reverse_geocode(man_lat, man_lon)
                st.session_state[stored_loc_key] = {
                    "lat": man_lat, "lon": man_lon,
                    "accuracy": man_acc, "address": address
                }
                st.rerun()

        stored_loc = st.session_state.get(stored_loc_key)
        if stored_loc:
            st.success(
                f"✅ **Location confirmed:** {stored_loc['address']}\n\n"
                f"📌 `{stored_loc['lat']:.5f}, {stored_loc['lon']:.5f}` "
                f"(±{stored_loc['accuracy']}m)"
            )

        st.markdown("---")

        # ── Step 2: Photo proof ──────────────────────────────────────
        st.markdown("**Step 2 — Capture or upload a photo**")
        st.caption("Take a selfie or photo showing you're at the lecture.")

        photo_file = st.file_uploader(
            "Camera / Gallery",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            key=f"photo_{d}_{subject}",
        )

        photo_b64 = None
        if photo_file:
            img_bytes = photo_file.read()
            photo_b64 = img_to_b64(img_bytes)
            st.markdown(
                f"<img src='data:image/jpeg;base64,{photo_b64}' "
                f"style='border-radius:8px;max-height:120px;margin-top:6px;'/>",
                unsafe_allow_html=True,
            )
            st.success("✅ Photo captured.")

        st.markdown("---")

        # ── Step 3: Confirm (STRICT) ─────────────────────────────────
        st.markdown("**Step 3 — Confirm attendance**")

        can_confirm = stored_loc is not None and photo_b64 is not None
        if not can_confirm:
            st.warning("⚠️ Both Location and a Photo are strictly required to mark attendance.")

        _, col_center, _ = st.columns([1, 2, 1])

        if col_center.button(
            "✅ Mark Attended (with proof)",
            key=f"att_proof_{d}_{subject}",
            use_container_width=True,
            type="primary",
            disabled=not can_confirm,
        ):
            with st.spinner("Encrypting & Uploading to Backend..."):
                # 1. Prepare the exact format FastAPI expects
                files = {
                    "photo": (photo_file.name, photo_file.getvalue(), photo_file.type)
                }
                data = {
                    "subject": subject,
                    "date": d.isoformat(),
                    "latitude": stored_loc["lat"],
                    "longitude": stored_loc["lon"],
                    "accuracy": stored_loc["accuracy"],
                    "address": stored_loc["address"]
                }
                
                # 2. Hit the FastAPI endpoint
                try:
                    res = requests.post("http://localhost:8000/api/v1/attendance/mark", data=data, files=files)
                    res.raise_for_status() # Check for 400/500 errors
                    api_result = res.json()
                    
                    # 3. Update local UI state with the Database response
                    proof = {
                        "timestamp": api_result["proof"]["timestamp"].replace("T", " ")[:16], # Clean up ISO format
                        "lat": api_result["proof"]["latitude"],
                        "lon": api_result["proof"]["longitude"],
                        "accuracy": api_result["proof"]["accuracy"],
                        "address": api_result["proof"]["address"],
                        "photo_url": api_result["proof"]["photo_url"], # Using URL now instead of heavy base64
                    }
                    
                    set_record(d, subject, ATT, proof)
                    
                    if stored_loc_key in st.session_state:
                        del st.session_state[stored_loc_key]
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"🚨 API Connection Failed: Make sure your FastAPI server is running! Error: {e}")

# ══════════════════════════════════════════════════════════════════════
# PAGE: DAY VIEW
# ══════════════════════════════════════════════════════════════════════

def page_day_view():
    d = st.session_state.viewed_date

    nav1, nav2, nav3 = st.columns([1, 5, 1])
    with nav1:
        if st.button("◀", use_container_width=True):
            st.session_state.viewed_date -= timedelta(days=1)
            st.rerun()
    with nav2:
        st.markdown(
            f"<h3 style='text-align:center;color:#F3F4F6;font-family:Georgia,serif;margin:0;'>"
            f"{d.strftime('%A, %d %b %Y')}</h3>",
            unsafe_allow_html=True,
        )
    with nav3:
        if st.button("▶", use_container_width=True):
            st.session_state.viewed_date += timedelta(days=1)
            st.rerun()

    picked = st.date_input("Jump to date", value=d, label_visibility="collapsed")
    if picked != d:
        st.session_state.viewed_date = picked
        st.rerun()

    st.divider()

    subjects_today = subjects_on_day(d)
    if not subjects_today:
        st.info(f"📭 No classes scheduled on {get_day_name(d)}s. Edit timetable to add subjects.")
        return

    st.markdown(f"**{get_day_name(d)} · {len(subjects_today)} class(es)**")

    # Bulk actions (All Attended removed for strict proof enforcement)
    bb, bc, bd = st.columns(3)
    if bb.button("— All Off", use_container_width=True):
        for s in subjects_today:
            set_record(d, s, OFF)
        st.rerun()
    if bc.button("❌ All Missed", use_container_width=True):
        for s in subjects_today:
            set_record(d, s, MISS)
        st.rerun()
    if bd.button("○ Clear All", use_container_width=True):
        for s in subjects_today:
            set_record(d, s, CLEAR)
        st.rerun()

    st.divider()

    for subject in subjects_today:
        record = get_record(d, subject)
        current_status = record["status"]
        has_proof = record["proof"] is not None
        stats = subject_stats(subject)

        pct_color = "#22c55e" if stats["pct"] >= st.session_state.target_attendance else "#ef4444"
        pct_display = f"{stats['pct']:.2f}" if stats["total"] > 0 else "—"

        proof_badge = (
            "<span style='background:#dcfce7;color:#166534;font-size:.65rem;"
            "padding:2px 7px;border-radius:20px;margin-left:8px;font-weight:600;'>📍 PROOF</span>"
            if has_proof and current_status == ATT else ""
        )

        st.markdown(
            f"""
            <div style='background:#1E1E1E;border-radius:12px;padding:14px 16px;
                        border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);margin-bottom:4px;'>
                <div style='display:flex;align-items:center;gap:14px;'>
                    <div style='text-align:center;min-width:54px;'>
                        <div style='font-size:1.25rem;font-weight:800;color:{pct_color};
                                    font-family:Georgia,serif;'>{pct_display}</div>
                        <div style='font-size:.65rem;color:#9CA3AF;border-top:1px solid #374151;
                                    padding-top:2px;'>{st.session_state.target_attendance:.0f}</div>
                    </div>
                    <div style='flex:1;'>
                        <div style='font-weight:700;font-size:.95rem;color:#F3F4F6;'>
                            {subject}{proof_badge}
                        </div>
                        <div style='font-size:.76rem;color:#9CA3AF;margin-top:3px;'>
                            {stats["attended"]}/{stats["total"]} attended ·
                            {"can miss <b style='color:#22c55e;'>" + str(stats["can_miss"]) + "</b> more"
                              if stats["pct"] >= st.session_state.target_attendance else
                              "need <b style='color:#ef4444;'>" + str(stats["need"]) + "</b> to recover"}
                        </div>
                    </div>
                    <div style='color:{STATUS_COLORS.get(current_status,"#6b7280")};
                                font-size:.78rem;font-weight:600;'>
                        {STATUS_LABELS.get(current_status,"○ Not marked")}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        b1, b2, b3, b4 = st.columns(4)
        key = f"{d.isoformat()}_{subject}"

        if b1.button("○ Clear", key=f"{key}_clr", use_container_width=True):
            set_record(d, subject, CLEAR)
            st.rerun()
        if b2.button("— Off", key=f"{key}_off", use_container_width=True):
            set_record(d, subject, OFF)
            st.rerun()
        if b3.button("❌ Missed", key=f"{key}_miss", use_container_width=True):
            set_record(d, subject, MISS)
            st.rerun()

        # Strict visual indicator - forcing use of the expander
        if current_status == ATT and has_proof:
            b4.button("✅ Verified", key=f"{key}_verified_btn", disabled=True, use_container_width=True)
        else:
            b4.button("⬇️ Expand to Mark", key=f"{key}_expand_btn", disabled=True, use_container_width=True)

        render_verified_mark_section(d, subject)
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# PAGE: TIMETABLE
# ══════════════════════════════════════════════════════════════════════

def page_timetable():
    st.markdown("""
        <h2 style='font-family:Georgia,serif;color:#F3F4F6;margin-bottom:.25rem;'>
            📋 Weekly Timetable
        </h2>
        <p style='color:#9CA3AF;font-size:.9rem;margin-top:0;'>
            Set which subjects you have on each day of the week.
        </p>
    """, unsafe_allow_html=True)

    st.divider()

    with st.expander("⚙️ Manage Subjects", expanded=False):
        new_sub = st.text_input("Add subject", placeholder="e.g. Data Structures")
        if st.button("➕ Add", use_container_width=True) and new_sub.strip():
            if new_sub.strip() not in st.session_state.subjects:
                st.session_state.subjects.append(new_sub.strip())
                st.rerun()
        to_del = st.selectbox("Remove subject", ["—"] + st.session_state.subjects)
        if st.button("🗑️ Remove", use_container_width=True) and to_del != "—":
            st.session_state.subjects.remove(to_del)
            for day in DAYS:
                if to_del in st.session_state.timetable.get(day, []):
                    st.session_state.timetable[day].remove(to_del)
            st.rerun()

    tabs = st.tabs(DAY_SHORT)
    for i, day in enumerate(DAYS):
        with tabs[i]:
            current = st.session_state.timetable.get(day, [])
            updated = st.multiselect(
                f"Classes on {day}",
                options=st.session_state.subjects,
                default=current,
                label_visibility="collapsed",
                key=f"tt_{day}",
            )
            st.session_state.timetable[day] = updated
            st.caption(f"{len(updated)} class(es) on {day}")

    st.success("✅ Timetable auto-saved.")

    st.markdown("---")
    st.markdown("#### Weekly Preview")
    max_slots = max((len(v) for v in st.session_state.timetable.values()), default=0)
    if max_slots == 0:
        st.info("No classes scheduled yet.")
        return
    header_cols = st.columns(7)
    for ci, d in enumerate(DAY_SHORT):
        header_cols[ci].markdown(f"**{d}**")
    for slot in range(max_slots):
        cols = st.columns(7)
        for ci, day in enumerate(DAYS):
            day_subjects = st.session_state.timetable.get(day, [])
            if slot < len(day_subjects):
                cols[ci].markdown(
                    f"<div style='background:#374151;border-radius:6px;padding:5px 7px;"
                    f"font-size:.72rem;color:#93c5fd;margin-bottom:3px;'>{day_subjects[slot]}</div>",
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════════════════
# PAGE: SUBJECTS
# ══════════════════════════════════════════════════════════════════════

def trigger_low_attendance_email(user_email, current_pct, target_pct):
    if not st.session_state.has_warning_email_been_sent:
        print(f"[MOCK SMTP] Dispatching WARNING email to {user_email}: Attendance {current_pct:.2f}% is below target {target_pct:.0f}%!")
        st.session_state.has_warning_email_been_sent = True

def page_subjects():
    st.markdown("<h4 style='color:#F3F4F6;'>⚙️ Tracking Goal</h4>", unsafe_allow_html=True)
    new_target = st.slider("Set Minimum Attendance Goal (%)", min_value=1.0, max_value=100.0, value=float(st.session_state.target_attendance), step=1.0)
    
    if new_target != st.session_state.target_attendance:
        st.session_state.target_attendance = new_target
        # Reset email flag so if they drop below the *new* target, they get warned again:
        st.session_state.has_warning_email_been_sent = False
        st.rerun()

    overall = overall_stats()
    
    # ── Automated Warning System ──
    if overall["total"] > 0 and overall["pct"] < st.session_state.target_attendance:
        st.markdown(f"""
        <div style='background:rgba(239, 68, 68, 0.15); border:1px solid #ef4444; border-radius:8px; padding:12px; margin-bottom:16px; color:#fca5a5; font-size:0.95rem; display:flex; align-items:center; gap:10px;'>
            <span style='font-size:1.2rem;'>🚨</span>
            <b>Warning:</b> Your overall attendance ({overall['pct']:.2f}%) has fallen below your target of {st.session_state.target_attendance:.0f}%.
        </div>
        """, unsafe_allow_html=True)
        trigger_low_attendance_email("student@scholara.edu", overall['pct'], st.session_state.target_attendance)

    ov_color = "#22c55e" if overall["pct"] >= st.session_state.target_attendance else "#ef4444"

    st.markdown(
        f"""
        <div style='background:linear-gradient(135deg,#1E1E1E,#121212);
                    border-radius:16px;padding:20px 24px;border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);
                    margin-bottom:1rem;display:flex;justify-content:space-between;align-items:center;'>
            <div>
                <div style='color:#9CA3AF;font-size:.85rem;'>Overall Attendance</div>
                <div style='font-size:2.2rem;font-weight:800;color:{ov_color};
                            font-family:Georgia,serif;'>{overall["pct"]:.2f}%</div>
                <div style='color:#9CA3AF;font-size:.8rem;'>
                    {overall["attended"]} attended / {overall["total"]} total ·
                    {overall["missed"]} missed · {overall["off"]} off
                </div>
            </div>
            <div style='font-size:3rem;'>{"🎓" if overall["pct"] >= st.session_state.target_attendance else "⚠️"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    subjects_with_data = [s for s in st.session_state.subjects if subject_stats(s)["total"] > 0]
    subjects_sorted = sorted(subjects_with_data, key=lambda s: subject_stats(s)["pct"])

    if not subjects_sorted:
        st.info("No attendance data yet. Start marking in Day View.")
        return

    for subject in subjects_sorted:
        s = subject_stats(subject)
        pct_color = "#22c55e" if s["pct"] >= st.session_state.target_attendance else "#ef4444"

        proof_count = sum(
            1 for day_data in st.session_state.attendance_log.values()
            if day_data.get(subject, {}).get("proof") is not None
        )

        st.markdown(
            f"""
            <div style='background:#1E1E1E;border-radius:12px;padding:16px 18px;
                        border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);margin-bottom:10px;'>
                <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                    <div>
                        <div style='font-weight:700;font-size:1rem;color:#F3F4F6;'>
                            {subject}
                            {"<span style='background:#0c3350;color:#0284c7;font-size:.65rem;" +
                             "padding:2px 7px;border-radius:20px;margin-left:8px;'>📍 " +
                             str(proof_count) + " proofs</span>" if proof_count > 0 else ""}
                        </div>
                        <div style='font-size:.78rem;color:#9CA3AF;margin-top:4px;'>
                            {s["attended"]}/{s["total"]} attended ·
                            {s["missed"]} missed · {s["off"]} off
                        </div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='font-size:1.5rem;font-weight:800;color:{pct_color};
                                    font-family:Georgia,serif;'>{s["pct"]:.2f}%</div>
                        <div style='font-size:.72rem;color:#9CA3AF;'>req. {st.session_state.target_attendance:.0f}%</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(min(s["pct"] / 100, 1.0))
        if s["pct"] >= st.session_state.target_attendance:
            st.success(f"✅ Safe! Can miss **{s['can_miss']}** more lecture(s).")
        else:
            st.error(f"🚨 **{round(st.session_state.target_attendance - s['pct'], 2)}% below target.** Attend next **{s['need']}** class(es) to recover.")
        st.markdown("")

# ══════════════════════════════════════════════════════════════════════
# PAGE: CALENDAR
# ══════════════════════════════════════════════════════════════════════

def page_calendar():
    st.markdown("""<h2 style='font-family:Georgia,serif;color:#F3F4F6;margin-bottom:.5rem;'>
        🗓️ Calendar</h2>""", unsafe_allow_html=True)

    cm1, cm2, cm3 = st.columns([1, 4, 1])
    with cm1:
        if st.button("◀", key="cal_prev"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12; st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()
    with cm2:
        st.markdown(
            f"<h3 style='text-align:center;color:#F3F4F6;font-family:Georgia,serif;margin:0;'>"
            f"{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>",
            unsafe_allow_html=True,
        )
    with cm3:
        if st.button("▶", key="cal_next"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1; st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()

    st.divider()

    year, month = st.session_state.cal_year, st.session_state.cal_month
    hcols = st.columns(7)
    for i, d in enumerate(DAY_SHORT):
        hcols[i].markdown(
            f"<div style='text-align:center;color:#9CA3AF;font-size:.78rem;font-weight:600;'>{d}</div>",
            unsafe_allow_html=True,
        )

    today = date.today()
    for week in calendar.monthcalendar(year, month):
        wcols = st.columns(7)
        for wi, day_num in enumerate(week):
            if day_num == 0:
                wcols[wi].markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
                continue
            d = date(year, month, day_num)
            dot_color = day_dot_color(d)
            is_today = d == today
            if wcols[wi].button(str(day_num), key=f"cal_{d.isoformat()}", use_container_width=True):
                st.session_state.viewed_date = d
                st.session_state.active_page = "🧭 Day View"
                st.rerun()
            wcols[wi].markdown(
                f"<div style='text-align:center;margin-top:-8px;'>"
                f"<span style='color:{dot_color};font-size:9px;'>{'◉' if is_today else '●'}</span></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    _, days_in_month = calendar.monthrange(year, month)
    all_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    not_marked = off_days = missed_days = attended_days = mixed_days = 0
    month_total = month_att = month_miss = month_off = 0
    proof_count = 0

    for d in all_dates:
        subs = subjects_on_day(d)
        if not subs:
            off_days += 1
            continue
        statuses = [get_status(d, s) for s in subs]
        marked = [s for s in statuses if s is not None]
        if not marked: not_marked += 1
        elif all(s == OFF for s in marked): off_days += 1
        elif all(s == ATT for s in marked): attended_days += 1
        elif all(s in (MISS, OFF) for s in marked) and any(s == MISS for s in marked): missed_days += 1
        else: mixed_days += 1

        for sub in subs:
            rec = get_record(d, sub)
            s = rec["status"]
            if s == ATT: month_total += 1; month_att += 1
            elif s == MISS: month_total += 1; month_miss += 1
            elif s == OFF: month_off += 1
            if rec["proof"]: proof_count += 1

    month_pct = round(month_att / month_total * 100, 2) if month_total > 0 else 0.0
    pct_color = "#22c55e" if month_pct >= st.session_state.target_attendance else "#ef4444"

    sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
    for col, val, label, color in [
        (sc1, not_marked, "Unmarked", "#6b7280"),
        (sc2, off_days, "Off", "#f59e0b"),
        (sc3, missed_days, "Missed", "#ef4444"),
        (sc4, attended_days, "Attended", "#22c55e"),
        (sc5, mixed_days, "Mixed", "#8b5cf6"),
        (sc6, proof_count, "📍 Proofs", "#38bdf8"),
    ]:
        col.markdown(
            f"<div style='text-align:center;background:#1E1E1E;border-radius:10px;"
            f"padding:10px 4px;border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);'>"
            f"<div style='font-size:1.3rem;font-weight:800;color:{color};'>{val}</div>"
            f"<div style='font-size:.65rem;color:#9CA3AF;margin-top:2px;'>{label}</div>"
            f"</div>", unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)
    lc1, lc2, lc3, lc4, lc5 = st.columns(5)
    for col, val, label, color in [
        (lc1, month_off, "Off", "#f59e0b"),
        (lc2, month_miss, "Missed", "#ef4444"),
        (lc3, month_att, "Attended", "#22c55e"),
        (lc4, month_total, "Total", "#94a3b8"),
        (lc5, f"{month_pct}%", "Percent", pct_color),
    ]:
        col.markdown(
            f"<div style='text-align:center;background:#1E1E1E;border-radius:10px;"
            f"padding:10px 4px;border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);'>"
            f"<div style='font-size:1.3rem;font-weight:800;color:{color};'>{val}</div>"
            f"</div>", unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════════
# PAGE: STUDY ASSISTANT
# ══════════════════════════════════════════════════════════════════════

def mock_llm_stream(prompt: str) -> Generator[str, None, None]:
    response = (
        f"Great question about '{prompt[:55]}{'...' if len(prompt)>55 else ''}'! "
        "Based on your uploaded study material, the retrieved excerpt explains this "
        "concept clearly. The key idea is foundational and will help with both "
        "theory and numerical problems in your exams. Review the source snippet "
        "below for context, and cross-reference with your lecture notes. "
        "Ask me to elaborate on any specific part! 📚"
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.035)

def page_study_assistant():
    st.markdown("""<h2 style='font-family:Georgia,serif;color:#F3F4F6;margin-bottom:.25rem;'>
        🤖 AI Study Assistant</h2>
        <p style='color:#9CA3AF;font-size:.9rem;margin-top:0;'>
        Upload your PDF (sidebar) and ask questions grounded in your notes.</p>
    """, unsafe_allow_html=True)
    doc = st.session_state.uploaded_doc
    if doc["loaded"]:
        st.info(f"📖 **Active:** `{doc['filename']}` — Ready!")
    else:
        st.warning("⬅️ Upload a PDF in the sidebar to enable document-grounded answers.")
    st.divider()
    if not st.session_state.chat_history:
        with st.chat_message("assistant", avatar="🎓"):
            st.markdown("**Hello!** Upload your PDF and ask study questions.\n\n_e.g. 'Explain Newton's laws'_")
    assistant_idx = 0
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🎓"):
                st.markdown(msg["content"])
                if assistant_idx < len(st.session_state.source_snippets):
                    snippet = st.session_state.source_snippets[assistant_idx]
                    if snippet:
                        with st.expander("📄 Source Snippet"):
                            st.markdown(f"**Page {snippet['page']}** — `{doc.get('filename','doc.pdf')}`")
                            st.markdown(f"> _{snippet['snippet']}_")
                assistant_idx += 1
    query = st.chat_input("Ask about your study material…")
    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user", avatar="👤"):
            st.markdown(query)
        snippet = random.choice(MOCK_SNIPPETS) if doc["loaded"] else None
        with st.chat_message("assistant", avatar="🎓"):
            response = st.write_stream(mock_llm_stream(query))
            if snippet:
                with st.expander("📄 Source Snippet"):
                    st.markdown(f"**Page {snippet['page']}** — `{doc['filename']}`")
                    st.markdown(f"> _{snippet['snippet']}_")
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.session_state.source_snippets.append(snippet)
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.source_snippets = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════

def render_sidebar() -> str:
    with st.sidebar:
        overall = overall_stats()
        ov_color = "#22c55e" if overall["pct"] >= st.session_state.target_attendance else "#ef4444"
        st.markdown(
            f"""<div style='text-align:center;padding:1rem 0 .5rem;'>
                <div style='font-size:2.2rem;'>🎓</div>
                <h1 style='font-family:Georgia,serif;font-size:1.6rem;color:#F3F4F6;
                           margin:.2rem 0 0;font-weight:800;'>Scholara</h1>
                <p style='color:#9CA3AF;font-size:.72rem;margin:.15rem 0 .6rem;'>
                    Academic Productivity Suite v3
                </p>
                <div style='background:#1E1E1E;border-radius:10px;padding:8px 12px;
                            border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);display:inline-block;'>
                    <span style='color:{ov_color};font-weight:800;font-size:1.1rem;'>
                        {overall["pct"]:.2f}%
                    </span>
                    <span style='color:#9CA3AF;font-size:.75rem;'> | {st.session_state.target_attendance:.0f}%</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.divider()
        page = st.radio(
            "Navigate",
            ["🧭 Day View", "⏳ Timetable", "📆 Calendar", "📈 Subjects", "🎯 Focus Time", "🧠 Study Assistant"],
            label_visibility="collapsed",
            key="active_page",
        )
        st.divider()
        st.markdown("### 📂 Study Materials")
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
        if uploaded_file:
            if not st.session_state.uploaded_doc["loaded"] or \
               st.session_state.uploaded_doc["filename"] != uploaded_file.name:
                with st.spinner("Indexing…"):
                    time.sleep(0.8)
                st.session_state.uploaded_doc = {"loaded": True, "filename": uploaded_file.name}
            st.success(f"✅ {uploaded_file.name}")
            if st.button("🗑️ Remove", use_container_width=True):
                st.session_state.uploaded_doc = {"loaded": False, "filename": None}
                st.rerun()
        else:
            if st.session_state.uploaded_doc["loaded"]:
                st.session_state.uploaded_doc = {"loaded": False, "filename": None}
        st.divider()
        st.caption("Scholara v3.0 · Strict Proof Mode\nBuilt with Streamlit")
    return page

# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="Scholara v3 — GPS Attendance",
        page_icon="📍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
        html, body, [class*="css"] { font-family:'IBM Plex Sans',sans-serif; background:#121212; color:#F3F4F6; }
        .stApp { background-color:#121212; }
        [data-testid="stSidebar"] { 
            background:#1E1E1E; 
            border-right:1px solid #374151; 
            transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1) !important;
        }
        
        /* Global Button Micro-interactions (Attendance Marker "Pop") */
        .stButton>button { 
            border-radius:8px;font-weight:600;font-size:.82rem;border:1px solid #cbd5e1;
            box-shadow:0 4px 6px rgba(0,0,0,0.3);background:#1E1E1E;color:#E5E7EB;
            transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important; 
        }
        .stButton>button:hover { 
            background:#374151;color:#F3F4F6;border-color:#94a3b8; 
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
        }
        .stButton>button:active {
            transform: scale(0.94) translateY(2px) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
            transition: all 0.1s !important;
        }
        
        button[kind="primary"] { background:#2563eb!important;color:white!important;border-color:#2563eb!important; }
        .stTextInput input,.stNumberInput input,.stDateInput input { background:#1E1E1E!important;border:1px solid #cbd5e1!important;color:#F3F4F6!important;border-radius:8px!important; }
        [data-testid="stProgressBar"]>div>div { background:linear-gradient(90deg,#2563eb,#22c55e)!important; transition: width 0.4s ease; }
        [data-testid="stExpander"] { background:#1E1E1E;border:1px solid #374151;box-shadow:0 2px 4px rgba(0,0,0,0.02);border-radius:10px; transition: all 0.2s ease; }
        [data-testid="stExpander"]:hover { border-color: #4B5563; }
        [data-testid="stChatMessage"] { background:#1E1E1E;border-radius:12px;border:1px solid #374151;box-shadow:0 4px 6px rgba(0,0,0,0.3);margin-bottom:.5rem; }
        [data-baseweb="tab"] { color:#9CA3AF!important;font-weight:600; }
        [data-baseweb="tab"][aria-selected="true"] { color:#0284c7!important; }
        [data-baseweb="tag"] { background:#2563eb!important; }
        hr { border-color:#374151!important; }
        .main .block-container { padding-top:1.5rem;max-width:960px; }
        
        /* Smooth Upload Dropzone */
        [data-testid="stFileUploadDropzone"] {
            transition: all 0.3s ease-in-out !important;
        }
        [data-testid="stFileUploadDropzone"]:hover {
            border-color: #38bdf8 !important;
            background-color: rgba(56, 189, 248, 0.05) !important;
        }
        [data-testid="stFileUploadDropzone"]:active {
            transform: scale(0.98);
        }

        /* Route fade-in animation on navigation */
        @keyframes fadeInSlide {
            0% { opacity: 0; transform: translateY(10px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        [data-testid="stAppViewBlockContainer"] {
            animation: fadeInSlide 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Sidebar Navigation Typography & Animation Upgrade */
        div[data-testid="stSidebar"] div[role="radiogroup"] > label {
            padding: 12px 10px !important;
            cursor: pointer;
            transition: background 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] > label p {
            font-size: 1.25rem !important;
            font-weight: 600 !important;
            color: #E5E7EB !important;
            transition: opacity 0.2s ease;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: clip;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            background: #374151;
            border-radius: 8px;
            color: #F3F4F6 !important;
            transform: translateX(4px);
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] > label:active {
            transform: scale(0.97) translateX(0) !important;
        }

        /* Profile Component Top Right - Click Instead of Hover */
        details.scholara-profile-container {
            position: fixed;
            top: 14px;
            right: 80px; 
            z-index: 999999;
            font-family: inherit;
        }
        
        details.scholara-profile-container summary {
            width: 36px;
            height: 36px;
            background: #2563eb;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 2px solid white;
            transition: background 0.2s;
            list-style: none; /* Hide default arrow */
            outline: none;
        }

        /* Hide the triangle in webkit browsers */
        details.scholara-profile-container summary::-webkit-details-marker {
            display: none;
        }

        details.scholara-profile-container summary:hover {
            background: #1d4ed8;
        }

        .scholara-dropdown {
            position: absolute;
            top: 46px;
            right: 0;
            width: 240px;
            background: #1E1E1E;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 16px;
            color: #F3F4F6;
            text-align: left;
            cursor: default;
            /* Dropdown is displayed automatically when <details> is open */
        }

        .profile-name {
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 4px;
            color: #F3F4F6;
        }

        .profile-role {
            font-size: 0.75rem;
            font-weight: 600;
            color: #2563eb;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #374151;
        }

        .profile-detail {
            font-size: 0.85rem;
            color: #9CA3AF;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .profile-menu-item {
            font-size: 0.9rem;
            color: #E5E7EB;
            margin-top: 12px;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            border-radius: 6px;
            transition: background 0.2s;
        }

        .profile-menu-item:hover {
            background: #374151;
        }
        </style>
        
        <details class="scholara-profile-container">
            <summary>SA</summary>
            <div class="scholara-dropdown">
                <div class="profile-name">Student Name</div>
                <div class="profile-role">Computer Science</div>
                <div class="profile-detail"><span>🎓</span> Roll No: 2023CS001</div>
                <div class="profile-detail"><span>✉️</span> student@scholara.edu</div>
                <div class="profile-detail"><span>📱</span> +91 9876543210</div>
                <hr style="margin: 8px 0 4px 0; border-color: #374151; border-style: solid; border-width: 1px 0 0 0;">
                <div class="profile-menu-item">
                    <span>⚙️</span> Manage Account
                </div>
            </div>
        </details>
    """, unsafe_allow_html=True)

    init_state()
    page = render_sidebar()

    if page == "🧭 Day View":          page_day_view()
    elif page == "⏳ Timetable":       page_timetable()
    elif page == "📆 Calendar":        page_calendar()
    elif page == "📈 Subjects":        page_subjects()
    elif page == "🎯 Focus Time":       page_focus_time()
    elif page == "🧠 Study Assistant": page_study_assistant()

if __name__ == "__main__":
    main()