from flask import Flask, request, redirect, url_for, flash, render_template_string, make_response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# Temporary storage
users = {
    "student": {},
    "teacher": {}
}

# ---------------- HOME ----------------
home_html = """
<!DOCTYPE html>
<html>
<head>
<title>Scholara</title>
<style>
body {
    margin: 0;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    background: #09090b;
    color: white;
    min-height: 100vh;
    overflow-x: hidden;
}
body::before, body::after {
    content: '';
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    z-index: -1;
    animation: float 10s ease-in-out infinite alternate;
}
body::before {
    width: 300px; height: 300px;
    background: rgba(220, 38, 38, 0.15);
    top: 20%; right: 20%;
}
body::after {
    width: 400px; height: 400px;
    background: rgba(37, 99, 235, 0.15);
    bottom: 10%; left: 10%;
    animation-delay: -5s;
}
@keyframes float {
    0% { transform: translateY(0px) scale(1); }
    100% { transform: translateY(-30px) scale(1.1); }
}

.header {
    text-align: center;
    padding: 20px;
    background: rgba(17, 24, 39, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 3px solid #2563eb;
}

.logo-title {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
}

.logo-title img {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    box-shadow: 0 0 10px rgba(255,255,255,0.3);
}

.logo-title h1 {
    margin: 0;
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #ffffff;
    text-shadow:
        1px 1px 0 #3b82f6,
        2px 2px 0 #2563eb,
        3px 3px 0 #1d4ed8,
        4px 4px 0 #1e40af,
        5px 5px 12px rgba(0,0,0,0.5);
}

.subtitle {
    color: #94a3b8;
    font-size: 14px;
}

.main {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 70vh;
}

.box {
    text-align: center;
    padding: 50px 60px;
    background: rgba(17, 24, 39, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
    border-radius: 20px;
}

button {
    padding: 12px 25px;
    margin: 10px;
    font-size: 16px;
    border-radius: 50px;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
}

.teacher {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    color: white;
    box-shadow: 0 5px 15px rgba(37, 99, 235, 0.4);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.teacher:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.6);
}

.student {
    background: linear-gradient(135deg, #10b981, #047857);
    color: white;
    box-shadow: 0 5px 15px rgba(16, 185, 129, 0.4);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.student:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.6);
}
</style>
</head>
<body>
<div class="header">
    <div class="logo-title">
        <img src="https://cdn-icons-png.flaticon.com/512/3135/3135755.png">
        <h1>Scholara</h1>
    </div>
    <div class="subtitle">Academic Productivity Suite v3</div>
</div>
<div class="main">
<div class="box">
<a href="/login/teacher"><button class="teacher">Faculty Login</button></a><br>
<a href="/login/student"><button class="student">Student Login</button></a>
</div>
</div>
</body>
</html>
"""

# ---------------- LOGIN (Updated with Checkbox) ----------------
login_html = """
<!DOCTYPE html>
<html>
<head>
<title>Login</title>
<style>
body {
    margin: 0;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    background: #09090b;
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    overflow: hidden;
}
.box {
    background: rgba(17, 24, 39, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
    padding: 40px;
    border-radius: 20px;
    width: 380px;
}
input[type="text"], input[type="password"] {
    width: 100%;
    padding: 12px;
    margin: 10px 0;
    border-radius: 8px;
    border: none;
    box-sizing: border-box;
}
.remember-me {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 10px 0;
    font-size: 14px;
    color: #94a3b8;
    cursor: pointer;
}
button {
    width: 100%;
    padding: 12px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
}
a { color: #60a5fa; display: block; text-align: center; margin-top: 10px; text-decoration: none; }
h2 { text-align: center; font-size: 32px; color: white; }
</style>
</head>
<body>
<div class="box">
<h2>{{ role.capitalize() }} Login</h2>

{% with messages = get_flashed_messages() %}
  {% if messages %}{% for message in messages %}<p style="color:red; text-align:center;">{{ message }}</p>{% endfor %}{% endif %}
{% endwith %}

<form method="POST">
    <input type="text" name="username" placeholder="Username" value="{{ remembered_user }}" required>
    <input type="password" name="password" placeholder="Password" required>
    
    <label class="remember-me">
        <input type="checkbox" name="remember"> Remember Me
    </label>

    <button type="submit">Login</button>
</form>

<a href="/signup/{{ role }}">Create Account</a>
<a href="/">⬅ Back</a>
</div>
</body>
</html>
"""

# ---------------- SIGNUP ----------------
signup_html = """
<!DOCTYPE html>
<html>
<head>
<title>Signup</title>
<style>
body {
    margin: 0;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    background: #09090b;
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}
.box {
    background: rgba(17, 24, 39, 0.6);
    padding: 40px;
    border-radius: 20px;
    width: 380px;
}
input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; box-sizing: border-box; }
button { width: 100%; padding: 12px; background: #10b981; color: white; border: none; border-radius: 8px; cursor: pointer; }
h2 { text-align: center; }
a { color: #60a5fa; display: block; text-align: center; margin-top: 10px; text-decoration: none; }
</style>
</head>
<body>
<div class="box">
<h2>{{ role.capitalize() }} Signup</h2>
<form method="POST">
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Create Account</button>
</form>
<a href="/">⬅ Back</a>
</div>
</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template_string(home_html)

@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in users:
        return "Invalid role", 404

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = request.form.get("remember") # 'on' if checked

        if username in users[role] and check_password_hash(users[role][username], password):
            # Create a response to set cookies
            resp = make_response(f"{role.capitalize()} Login Successful!")
            
            if remember:
                # Store username in cookie for 30 days
                resp.set_cookie('remembered_user', username, max_age=30*24*60*60)
            else:
                # Delete cookie if they didn't check the box
                resp.delete_cookie('remembered_user')
            
            return resp
        else:
            flash("Invalid Credentials")

    # On GET, retrieve the remembered username from cookies
    remembered_user = request.cookies.get('remembered_user', '')
    return render_template_string(login_html, role=role, remembered_user=remembered_user)

@app.route("/signup/<role>", methods=["GET", "POST"])
def signup(role):
    if role not in users:
        return "Invalid role", 404

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users[role]:
            flash("User already exists!")
            return redirect(url_for("signup", role=role))

        users[role][username] = generate_password_hash(password)
        flash("Account Created Successfully!")
        return redirect(url_for("login", role=role))

    return render_template_string(signup_html, role=role)

if __name__ == "__main__":
    app.run(debug=True)