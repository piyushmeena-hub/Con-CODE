import streamlit as st
import pandas as pd
import sqlite3
import yagmail
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "concode.db")

# =====================================
# SETTINGS
# =====================================

st.set_page_config(
    page_title="Student Self-Tracking Portal",
    layout="wide"
)

THRESHOLD_DEFAULT = 75

# =====================================
# DATABASE
# =====================================

def init_db():
    # Database is initialized centrally via database/init_db.py now
    pass

def save_attendance(subject, attended, total):

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()

    c.execute(
        "DELETE FROM subject_attendance WHERE subject=?",
        (subject,)
    )

    c.execute(
        "INSERT INTO subject_attendance (subject, attended, total) VALUES (?,?,?)",
        (subject, attended, total)
    )

    conn.commit()
    conn.close()

# =====================================
# SESSION STATE
# =====================================

if "schedule" not in st.session_state:
    st.session_state.schedule = None

if "attendance" not in st.session_state:
    st.session_state.attendance = {}

if "threshold" not in st.session_state:
    st.session_state.threshold = THRESHOLD_DEFAULT

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "roll_number" not in st.session_state:
    st.session_state.roll_number = ""

# =====================================
# EMAIL FUNCTION
# =====================================

def send_email_alert(pct):

    try:

        yag = yagmail.SMTP(
            user="your_email@gmail.com",
            password="your_app_password"
        )

        yag.send(
            to="student_email@gmail.com",
            subject="Low Attendance Alert 🚨",
            contents=f"Your attendance is low: {pct:.2f}%"
        )

    except:
        pass

# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.title("🎓 Student Portal")

    # Student Profile

    st.markdown("### 👤 Student Profile")

    name = st.text_input(
        "Student Name",
        value=st.session_state.student_name
    )

    roll = st.text_input(
        "Roll Number",
        value=st.session_state.roll_number
    )

    if name:
        st.session_state.student_name = name

    if roll:
        st.session_state.roll_number = roll

    # Upload Schedule

    st.markdown("### 📅 Upload Schedule")

    uploaded_file = st.file_uploader(
        "Upload timetable (.csv)",
        type=["csv"]
    )

    if uploaded_file:

        df = pd.read_csv(uploaded_file)

        st.session_state.schedule = df

        st.success("Schedule Loaded!")

    # Attendance Threshold

    st.markdown("### 🚨 Alert Settings")

    threshold = st.slider(
        "Minimum Attendance %",
        50,
        100,
        st.session_state.threshold
    )

    st.session_state.threshold = threshold


# =====================================
# MAIN DASHBOARD
# =====================================

st.title("📊 Student Self-Tracking Dashboard")

if st.session_state.student_name:

    st.write(
        f"👤 Student: {st.session_state.student_name}"
    )

# =====================================
# SCHEDULE SECTION
# =====================================

if st.session_state.schedule is not None:

    df = st.session_state.schedule

    st.markdown("## 📅 Your Schedule")

    st.dataframe(df)

    subjects = df["Subject"].unique()

    # ==========================
    # ATTENDANCE MARKING
    # ==========================

    st.markdown("## ✅ Mark Attendance")

    selected_subject = st.selectbox(
        "Select Subject",
        subjects
    )

    col1, col2 = st.columns(2)

    if selected_subject not in st.session_state.attendance:

        st.session_state.attendance[selected_subject] = {
            "attended": 0,
            "total": 0
        }

    with col1:

        if st.button("Present"):

            st.session_state.attendance[selected_subject]["attended"] += 1
            st.session_state.attendance[selected_subject]["total"] += 1

    with col2:

        if st.button("Absent"):

            st.session_state.attendance[selected_subject]["total"] += 1

    # ==========================
    # CALCULATE ATTENDANCE
    # ==========================

    total_classes = 0
    attended_classes = 0

    for subject in st.session_state.attendance:

        att = st.session_state.attendance[subject]["attended"]
        tot = st.session_state.attendance[subject]["total"]

        save_attendance(subject, att, tot)

        total_classes += tot
        attended_classes += att

    if total_classes > 0:

        overall_pct = (
            attended_classes / total_classes
        ) * 100

    else:

        overall_pct = 0

    # ==========================
    # METRICS
    # ==========================

    st.markdown("## 📊 Attendance Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Attendance %",
        f"{overall_pct:.2f}%"
    )

    col2.metric(
        "Total Classes",
        total_classes
    )

    col3.metric(
        "Classes Attended",
        attended_classes
    )

    # ==========================
    # ALERT SYSTEM
    # ==========================

    threshold = st.session_state.threshold

    if overall_pct < threshold:

        st.error(
            f"🚨 LOW ATTENDANCE ALERT!\n"
            f"Your attendance is {overall_pct:.2f}%"
        )

        send_email_alert(overall_pct)

    else:

        st.success(
            f"✅ Attendance Safe ({overall_pct:.2f}%)"
        )

    # ==========================
    # SUBJECT TABLE
    # ==========================

    st.markdown("## 📋 Subject-wise Attendance")

    table_data = []

    for subject in subjects:

        att = st.session_state.attendance.get(
            subject,
            {"attended": 0}
        )["attended"]

        tot = st.session_state.attendance.get(
            subject,
            {"total": 0}
        )["total"]

        pct = (
            (att / tot) * 100
            if tot > 0 else 0
        )

        table_data.append(
            {
                "Subject": subject,
                "Attended": att,
                "Total": tot,
                "Percentage": f"{pct:.2f}%"
            }
        )

    table_df = pd.DataFrame(table_data)

    st.dataframe(table_df)

else:

    st.info(
        "Upload your schedule (.csv) from sidebar to start."
    )