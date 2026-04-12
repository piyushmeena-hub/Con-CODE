import streamlit as st
import json
import os
from werkzeug.security import check_password_hash

st.set_page_config(
    page_title="Scholara",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def _load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def render_login_ui():
    st.markdown("""
        <style>
        .stApp { background: #09090b; }
        .logo-row { display: flex; justify-content: center; align-items: center; gap: 12px; margin-bottom: 5px; margin-top: 10vh; }
        .logo-row img { width: 50px; height: 50px; border-radius: 50%; }
        .logo-row h1 {
            font-size: 42px; font-weight: 800; letter-spacing: 2px;
            color: white; margin: 0;
            text-shadow: 1px 1px 0 #3b82f6, 2px 2px 0 #2563eb, 3px 3px 0 #1d4ed8;
        }
        .subtitle { color: #94a3b8; font-size: 14px; text-align: center; margin-bottom: 40px; }
        .center-form { max-width: 400px; margin: 0 auto; background: rgba(17,24,39,0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); padding: 40px; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.3); }
        </style>
        <div class="logo-row">
            <img src="https://cdn-icons-png.flaticon.com/512/3135/3135755.png">
            <h1>Scholara</h1>
        </div>
        <div class="subtitle">Academic Productivity Suite v4</div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Sign In</h3>", unsafe_allow_html=True)
            role = st.selectbox("Role", ["Student", "Faculty"], label_visibility="collapsed")
            username = st.text_input("Username", placeholder="Username", label_visibility="collapsed").strip().lower()
            password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            submitted = st.form_submit_button("Launch Dashboard", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error("Please provide both username and password")
                    return

                users = _load_users()
                user = users.get(username)

                if not user:
                    st.error("Username not found")
                elif user["role"] != ("teacher" if role == "Faculty" else "student"):
                    st.error(f"This is not a {role} account.")
                elif not check_password_hash(user["password"], password):
                    st.error("Incorrect password")
                else:
                    st.session_state.authenticated = True
                    st.session_state.auth_username = username
                    st.session_state.auth_role = user["role"]
                    st.rerun()

def _check_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        render_login_ui()
        st.stop()

def main():
    _check_auth()

    role = st.session_state.auth_role
    
    if role == "student":
        import scholara_v3
        scholara_v3.main()
    elif role == "teacher":
        import frontend_teach
        frontend_teach.main()

if __name__ == "__main__":
    main()
