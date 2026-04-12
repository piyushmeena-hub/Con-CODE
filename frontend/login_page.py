"""
Scholara — Login / Signup Portal
Self-contained Flask app. No FastAPI dependency for auth.
Users stored in users.json next to this file.
On successful login → redirects to Streamlit with ?user=<username>&role=<role>
"""

import json
import os
from flask import Flask, flash, make_response, redirect, render_template_string, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "scholara-secret-2024"

STREAMLIT_URL = "http://localhost:8501"
USERS_FILE    = os.path.join(os.path.dirname(__file__), "users.json")

# ──────────────────────────────────────────────
# USER STORE  (flat JSON file — no DB needed)
# ──────────────────────────────────────────────

def _load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    # Default seed: one teacher account
    default = {
        "drsmith": {
            "password": generate_password_hash("faculty123"),
            "role": "teacher",
        }
    }
    _save_users(default)
    return default

def _save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ──────────────────────────────────────────────
# HTML TEMPLATES
# ──────────────────────────────────────────────

_BASE_STYLE = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    background: #09090b; color: white;
    min-height: 100vh; overflow-x: hidden;
}
body::before {
    content: ''; position: fixed; border-radius: 50%; filter: blur(80px);
    z-index: -1; width: 300px; height: 300px;
    background: rgba(220,38,38,0.15); top: 20%; right: 20%;
    animation: float 10s ease-in-out infinite alternate;
}
body::after {
    content: ''; position: fixed; border-radius: 50%; filter: blur(80px);
    z-index: -1; width: 400px; height: 400px;
    background: rgba(37,99,235,0.15); bottom: 10%; left: 10%;
    animation: float 10s ease-in-out infinite alternate; animation-delay: -5s;
}
@keyframes float {
    0%   { transform: translateY(0)    scale(1);   }
    100% { transform: translateY(-30px) scale(1.1); }
}
.header {
    text-align: center; padding: 20px;
    background: rgba(17,24,39,0.7); backdrop-filter: blur(12px);
    border-bottom: 3px solid #2563eb;
}
.logo-row { display: flex; justify-content: center; align-items: center; gap: 12px; }
.logo-row img { width: 50px; height: 50px; border-radius: 50%; }
.logo-row h1 {
    font-size: 42px; font-weight: 800; letter-spacing: 2px;
    text-shadow: 1px 1px 0 #3b82f6, 2px 2px 0 #2563eb,
                 3px 3px 0 #1d4ed8, 5px 5px 12px rgba(0,0,0,.5);
}
.subtitle { color: #94a3b8; font-size: 14px; margin-top: 6px; }
.center { display: flex; justify-content: center; align-items: center; min-height: 70vh; }
.card {
    background: rgba(17,24,39,0.6); backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 15px 35px rgba(0,0,0,0.3);
    border-radius: 20px; padding: 40px; width: 400px;
}
.card h2 { text-align: center; font-size: 28px; margin-bottom: 24px; }
input[type=text], input[type=password] {
    width: 100%; padding: 12px; margin: 8px 0;
    border-radius: 8px; border: none; font-size: 15px;
    background: #1e293b; color: white;
}
input[type=text]::placeholder, input[type=password]::placeholder { color: #64748b; }
.btn {
    display: block; width: 100%; padding: 13px; margin-top: 14px;
    border: none; border-radius: 8px; font-size: 15px;
    font-weight: 700; cursor: pointer; text-align: center;
    text-decoration: none; transition: transform .2s, box-shadow .2s;
}
.btn:hover { transform: translateY(-2px); }
.btn-blue  { background: linear-gradient(135deg,#3b82f6,#1d4ed8); color: white; box-shadow: 0 5px 15px rgba(37,99,235,.4); }
.btn-green { background: linear-gradient(135deg,#10b981,#047857); color: white; box-shadow: 0 5px 15px rgba(16,185,129,.4); }
.btn-pill  { border-radius: 50px; padding: 12px 28px; width: auto; display: inline-block; margin: 8px; }
.link { color: #60a5fa; display: block; text-align: center; margin-top: 12px; text-decoration: none; font-size: 14px; }
.link:hover { text-decoration: underline; }
.error { color: #f87171; text-align: center; margin-bottom: 10px; font-size: 14px; }
.remember { display: flex; align-items: center; gap: 8px; margin: 10px 0; color: #94a3b8; font-size: 14px; }
</style>
"""

home_html = f"""<!DOCTYPE html><html><head><title>Scholara</title>{_BASE_STYLE}</head><body>
<div class="header">
  <div class="logo-row">
    <img src="https://cdn-icons-png.flaticon.com/512/3135/3135755.png">
    <h1>Scholara</h1>
  </div>
  <div class="subtitle">Academic Productivity Suite v3</div>
</div>
<div class="center">
  <div class="card" style="text-align:center; padding: 50px 60px;">
    <p style="color:#94a3b8; margin-bottom:24px;">Choose your role to continue</p>
    <a href="/login/teacher"><button class="btn btn-blue btn-pill">🎓 Faculty Login</button></a>
    <a href="/login/student"><button class="btn btn-green btn-pill">📚 Student Login</button></a>
  </div>
</div>
</body></html>"""

login_html = f"""<!DOCTYPE html><html><head><title>Login</title>{_BASE_STYLE}</head><body>
<div class="header">
  <div class="logo-row">
    <img src="https://cdn-icons-png.flaticon.com/512/3135/3135755.png">
    <h1>Scholara</h1>
  </div>
</div>
<div class="center">
<div class="card">
  <h2>{{{{ role_label }}}} Login</h2>
  {{% for msg in messages %}}<p class="error">{{{{ msg }}}}</p>{{% endfor %}}
  <form method="POST">
    <input type="text"     name="username" placeholder="Username"
           value="{{{{ remembered }}}}" required>
    <input type="password" name="password" placeholder="Password" required>
    <label class="remember">
      <input type="checkbox" name="remember" {{{{ 'checked' if remembered }}}}> Remember Me
    </label>
    <button type="submit" class="btn btn-blue">Login</button>
  </form>
  <a class="link" href="/signup/{{{{ role }}}}">Don't have an account? Sign up</a>
  <a class="link" href="/">⬅ Back to home</a>
</div>
</div>
</body></html>"""

signup_html = f"""<!DOCTYPE html><html><head><title>Sign Up</title>{_BASE_STYLE}</head><body>
<div class="header">
  <div class="logo-row">
    <img src="https://cdn-icons-png.flaticon.com/512/3135/3135755.png">
    <h1>Scholara</h1>
  </div>
</div>
<div class="center">
<div class="card">
  <h2>{{{{ role_label }}}} Sign Up</h2>
  {{% for msg in messages %}}<p class="error">{{{{ msg }}}}</p>{{% endfor %}}
  <form method="POST">
    <input type="text"     name="username" placeholder="Choose a username" required>
    <input type="password" name="password" placeholder="Choose a password" required>
    <button type="submit" class="btn btn-green">Create Account</button>
  </form>
  <a class="link" href="/login/{{{{ role }}}}">Already have an account? Login</a>
  <a class="link" href="/">⬅ Back to home</a>
</div>
</div>
</body></html>"""

# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

@app.route("/")
def home():
    return render_template_string(home_html)


@app.route("/signup/<role>", methods=["GET", "POST"])
def signup(role):
    if role not in ("teacher", "student"):
        return "Invalid role", 404

    role_label = "Faculty" if role == "teacher" else "Student"
    messages   = []

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not password:
            messages.append("Username and password are required.")
        elif len(password) < 4:
            messages.append("Password must be at least 4 characters.")
        else:
            users = _load_users()
            if username in users:
                messages.append("Username already taken. Choose another.")
            else:
                users[username] = {
                    "password": generate_password_hash(password),
                    "role": role,
                }
                _save_users(users)
                # Redirect to login with success message in query param
                return redirect(f"/login/{role}?created=1")

    return render_template_string(signup_html, role=role, role_label=role_label, messages=messages)


@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in ("teacher", "student"):
        return "Invalid role", 404

    role_label = "Faculty" if role == "teacher" else "Student"
    messages   = []

    # Show success message after signup
    if request.args.get("created"):
        messages.append("✅ Account created! Please log in.")

    # Read remembered username from cookie
    remembered = request.cookies.get(f"remember_{role}", "")

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember")

        users = _load_users()
        user  = users.get(username)

        if not user:
            messages.append("Username not found.")
        elif user["role"] != role:
            messages.append(f"This account is not a {role_label} account.")
        elif not check_password_hash(user["password"], password):
            messages.append("Incorrect password.")
        else:
            # ✅ Login success — redirect to Streamlit with user info
            streamlit_url = f"{STREAMLIT_URL}/?user={username}&role={role}"
            resp = make_response(redirect(streamlit_url))

            if remember:
                resp.set_cookie(f"remember_{role}", username, max_age=30 * 24 * 60 * 60)
            else:
                resp.delete_cookie(f"remember_{role}")

            return resp

    return render_template_string(
        login_html,
        role=role, role_label=role_label,
        messages=messages, remembered=remembered,
    )


if __name__ == "__main__":
    print("🚀 Scholara Login Portal running at http://localhost:5000")
    print("   Default teacher → username: drsmith  password: faculty123")
    app.run(port=5000, debug=True)
