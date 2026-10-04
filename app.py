from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "talent-iq-production-key-change-later"

DATABASE = "talentiq.db"


# ================= DATABASE =================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'candidate',
            experience INTEGER DEFAULT 0,
            skills TEXT DEFAULT '',
            score INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            required_skills TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    jobs = [
        ("Senior Python Engineer", "Python,SQL,DSA,AWS"),
        ("Data Engineer", "Python,SQL,AWS,DSA"),
        ("Backend Engineer", "Python,Java,SQL,DSA")
    ]

    for title, skills in jobs:
        exists = conn.execute(
            "SELECT id FROM jobs WHERE title=?",
            (title,)
        ).fetchone()

        if not exists:
            conn.execute(
                "INSERT INTO jobs(title, required_skills) VALUES (?,?)",
                (title, skills)
            )

    conn.commit()
    conn.close()


init_db()


# ================= STYLE =================

STYLE = """
<style>
* {
    box-sizing:border-box;
    margin:0;
    padding:0;
    font-family:Arial,sans-serif;
}

body {
    background:#f5f7fb;
    color:#172033;
}

nav {
    background:#111827;
    color:white;
    padding:18px 7%;
    display:flex;
    justify-content:space-between;
    align-items:center;
}

.logo {
    font-size:25px;
    font-weight:bold;
    color:#8b7cff;
}

nav a {
    color:white;
    text-decoration:none;
    margin-left:20px;
}

.container {
    width:90%;
    max-width:1100px;
    margin:40px auto;
}

.hero {
    background:linear-gradient(135deg,#635bff,#8b5cf6);
    color:white;
    padding:70px 30px;
    text-align:center;
    border-radius:20px;
}

.hero h1 {
    font-size:48px;
    margin-bottom:15px;
}

.hero p {
    font-size:19px;
    margin-bottom:25px;
}

.btn {
    display:inline-block;
    background:#635bff;
    color:white;
    padding:12px 22px;
    border-radius:8px;
    text-decoration:none;
    border:none;
    cursor:pointer;
    margin-top:10px;
}

.white-btn {
    background:white;
    color:#635bff;
}

.card {
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 5px 20px rgba(0,0,0,.08);
    margin-bottom:20px;
}

.grid {
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
    gap:20px;
}

input, textarea, select {
    width:100%;
    padding:13px;
    margin:8px 0 15px;
    border:1px solid #ddd;
    border-radius:7px;
}

h1,h2,h3 {
    margin-bottom:15px;
}

table {
    width:100%;
    border-collapse:collapse;
    background:white;
}

th,td {
    padding:14px;
    border-bottom:1px solid #eee;
    text-align:left;
}

.badge {
    display:inline-block;
    background:#ede9fe;
    color:#5b21b6;
    padding:6px 10px;
    border-radius:20px;
    margin:3px;
}

.score {
    font-size:40px;
    font-weight:bold;
    color:#635bff;
}

.error {
    color:#dc2626;
    margin-bottom:15px;
}

.success {
    color:#16a34a;
    margin-bottom:15px;
}

footer {
    text-align:center;
    padding:30px;
    margin-top:50px;
    background:#111827;
    color:white;
}

@media(max-width:600px) {
    .hero h1 {
        font-size:35px;
    }

    nav {
        padding:15px;
    }

    nav a {
        margin-left:8px;
        font-size:13px;
    }
}
</style>
"""


# ================= NAVBAR =================

NAV = """
<nav>
    <div class="logo">🧠 TalentIQ</div>
    <div>
        <a href="/">Home</a>
        <a href="/jobs">Jobs</a>
        {% if session.get('user_id') %}
            <a href="/dashboard">Dashboard</a>
            {% if session.get('role') == 'recruiter' %}
                <a href="/recruiter">Recruiter</a>
            {% endif %}
            <a href="/logout">Logout</a>
        {% else %}
            <a href="/login">Login</a>
            <a href="/register">Register</a>
        {% endif %}
    </div>
</nav>
"""


def page(title, content):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title} - TalentIQ</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {STYLE}
    </head>
    <body>
        {NAV}
        <div class="container">
            {content}
        </div>
        <footer>
            TalentIQ © 2026 | Intelligent Recruitment & Candidate Analytics
        </footer>
    </body>
    </html>
    """


# ================= HOME =================

@app.route("/")
def home():

    return page("TalentIQ", """
    <div class="hero">
        <h1>TalentIQ</h1>
        <p>
            Intelligent Recruitment & Candidate Analytics Platform
        </p>
        <a class="btn white-btn" href="/register">Get Started</a>
        <a class="btn" href="/jobs">Explore Jobs</a>
    </div>

    <br><br>

    <div class="grid">

        <div class="card">
            <h3>🎯 Smart Matching</h3>
            <p>Match candidates with jobs using skills and experience.</p>
        </div>

        <div class="card">
            <h3>📊 Talent Scoring</h3>
            <p>Automatically calculate candidate performance scores.</p>
        </div>

        <div class="card">
            <h3>🏢 Recruiter Dashboard</h3>
            <p>Search, analyze and rank candidates efficiently.</p>
        </div>

        <div class="card">
            <h3>🧠 Skill Assessment</h3>
            <p>Evaluate candidate technical knowledge.</p>
        </div>

    </div>
    """)


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    error = ""

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            error = "All fields are required."

        else:
            conn = get_db()

            try:
                conn.execute("""
                    INSERT INTO users(name,email,password)
                    VALUES(?,?,?)
                """, (
                    name,
                    email,
                    generate_password_hash(password)
                ))

                conn.commit()
                conn.close()

                return redirect("/login")

            except sqlite3.IntegrityError:
                conn.close()
                error = "Email already registered."

    return page("Register", f"""
    <div class="card">
        <h2>Create Candidate Account</h2>

        <p class="error">{error}</p>

        <form method="POST">

            <label>Name</label>
            <input name="name" placeholder="Your full name" required>

            <label>Email</label>
            <input type="email" name="email" placeholder="Email" required>

            <label>Password</label>
            <input type="password" name="password" placeholder="Password" required>

            <button class="btn">Create Account</button>

        </form>
    </div>
    """)


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            return redirect("/dashboard")

        error = "Invalid email or password."

    return page("Login", f"""
    <div class="card">
        <h2>Login</h2>

        <p class="error">{error}</p>

        <form method="POST">

            <input type="email"
                   name="email"
                   placeholder="Email"
                   required>

            <input type="password"
                   name="password"
                   placeholder="Password"
                   required>

            <button class="btn">Login</button>

        </form>

        <br>
        <p>New user? <a href="/register">Create account</a></p>
    </div>
    """)


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    jobs = conn.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    conn.close()

    skills = [
        s.strip()
        for s in user["skills"].split(",")
        if s.strip()
    ]

    skills_html = ""

    for skill in skills:
        skills_html += f'<span class="badge">{skill}</span>'

    return page("Dashboard", f"""

    <h1>Welcome, {user["name"]} 👋</h1>

    <div class="grid">

        <div class="card">
            <h3>Talent Score</h3>
            <div class="score">{user["score"]}/100</div>
        </div>

        <div class="card">
            <h3>Experience</h3>
            <div class="score">{user["experience"]}</div>
            <p>Years</p>
        </div>

        <div class="card">
            <h3>Skills</h3>
            {skills_html if skills_html else "<p>No skills added yet.</p>"}
        </div>

    </div>

    <div class="card">
        <h2>Update Profile</h2>

        <form method="POST" action="/profile">

            <label>Experience in years</label>
            <input type="number"
                   name="experience"
                   min="0"
                   max="50"
                   value="{user["experience"]}">

            <label>Skills</label>
            <input name="skills"
                   value="{user["skills"]}"
                   placeholder="Python, SQL, DSA, AWS">

            <button class="btn">
                Save Profile
            </button>

        </form>
    </div>

    <div class="card">
        <h2>Skill Assessment</h2>

        <p>Take the assessment to improve your TalentIQ score.</p>

        <a class="btn" href="/assessment">
            Start Assessment
        </a>

    </div>

    <div class="card">
        <h2>Recommended Jobs</h2>

        <p>
            <a class="btn" href="/jobs">View Jobs</a>
        </p>

    </div>
    """)


# ================= PROFILE =================

@app.route("/profile", methods=["POST"])
def profile():

    if not session.get("user_id"):
        return redirect("/login")

    experience = request.form.get("experience", 0)
    skills = request.form.get("skills", "")

    try:
        experience = int(experience)
    except:
        experience = 0

    skill_count = len([
        x for x in skills.split(",")
        if x.strip()
    ])

    score = min(
        100,
        experience * 5 + skill_count * 8
    )

    conn = get_db()

    conn.execute("""
        UPDATE users
        SET experience=?, skills=?, score=?
        WHERE id=?
    """, (
        experience,
        skills,
        score,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= ASSESSMENT =================

@app.route("/assessment", methods=["GET", "POST"])
def assessment():

    if not session.get("user_id"):
        return redirect("/login")

    if request.method == "POST":

        answers = request.form

        correct = 0

        if answers.get("q1") == "python":
            correct += 1

        if answers.get("q2") == "sql":
            correct += 1

        if answers.get("q3") == "dsa":
            correct += 1

        if answers.get("q4") == "aws":
            correct += 1

        if answers.get("q5") == "git":
            correct += 1

        score = correct * 20

        conn = get_db()

        conn.execute("""
            INSERT INTO assessments(user_id,score)
            VALUES(?,?)
        """, (
            session["user_id"],
            score
        ))

        conn.execute("""
            UPDATE users
            SET score = CASE
                WHEN score > ? THEN score
                ELSE ?
            END
            WHERE id=?
        """, (
            score,
            score,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return page("Assessment Result", f"""
        <div class="card">
            <h1>Assessment Complete 🎉</h1>

            <div class="score">{score}/100</div>

            <p>You answered {correct} out of 5 correctly.</p>

            <a class="btn" href="/dashboard">
                Back to Dashboard
            </a>
        </div>
        """)

    return page("Assessment", """
    <div class="card">

    <h1>TalentIQ Skill Assessment</h1>

    <form method="POST">

    <h3>1. Which language is commonly used for AI?</h3>

    <select name="q1" required>
        <option value="">Select</option>
        <option value="python">Python</option>
        <option value="html">HTML</option>
        <option value="css">CSS</option>
    </select>

    <h3>2. Which language is used for database queries?</h3>

    <select name="q2" required>
        <option value="">Select</option>
        <option value="java">Java</option>
        <option value="sql">SQL</option>
        <option value="python">Python</option>
    </select>

    <h3>3. What does DSA stand for?</h3>

    <select name="q3" required>
        <option value="">Select</option>
        <option value="dsa">Data Structures and Algorithms</option>
        <option value="database">Database System</option>
        <option value="design">Design System</option>
    </select>

    <h3>4. AWS is a:</h3>

    <select name="q4" required>
        <option value="">Select</option>
        <option value="aws">Cloud platform</option>
        <option value="language">Programming language</option>
        <option value="database">Database</option>
    </select>

    <h3>5. Git is mainly used for:</h3>

    <select name="q5" required>
        <option value="">Select</option>
        <option value="git">Version control</option>
        <option value="design">UI design</option>
        <option value="database">Database management</option>
    </select>

    <button class="btn">
        Submit Assessment
    </button>

    </form>

    </div>
    """)


# ================= JOBS =================

@app.route("/jobs")
def jobs():

    conn = get_db()

    jobs = conn.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    conn.close()

    cards = ""

    for job in jobs:

        skills = job["required_skills"].split(",")

        skill_html = ""

        for skill in skills:
            skill_html += f'<span class="badge">{skill}</span>'

        cards += f"""
        <div class="card">

            <h2>{job["title"]}</h2>

            <p><b>Required Skills</b></p>

            {skill_html}

            <br>

            <a class="btn"
               href="/match/{job["id"]}">
               Match Candidates
            </a>

        </div>
        """

    return page("Jobs", f"""
    <h1>Available Jobs</h1>
    <div class="grid">
        {cards}
    </div>
    """)


# ================= MATCHING =================

@app.route("/match/<int:job_id>")
def match(job_id):

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?",
        (job_id,)
    ).fetchone()

    users = conn.execute("""
        SELECT * FROM users
        WHERE role='candidate'
        ORDER BY score DESC
    """).fetchall()

    conn.close()

    required = [
        x.strip().lower()
        for x in job["required_skills"].split(",")
    ]

    rows = ""

    results = []

    for user in users:

        candidate_skills = [
            x.strip().lower()
            for x in user["skills"].split(",")
            if x.strip()
        ]

        matched = len(
            set(required) & set(candidate_skills)
        )

        percentage = 0

        if required:
            percentage = int(
                matched / len(required) * 100
            )

        final_score = int(
            percentage * 0.7 +
            user["score"] * 0.3
        )

        results.append(
            (final_score, user, percentage)
        )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    for rank, (score, user, percentage) in enumerate(results, 1):

        rows += f"""
        <tr>
            <td>{rank}</td>
            <td>{user["name"]}</td>
            <td>{user["experience"]} yrs</td>
            <td>{percentage}%</td>
            <td><b>{score}%</b></td>
        </tr>
        """

    return page("Candidate Matching", f"""

    <h1>{job["title"]}</h1>

    <div class="card">
        <h3>Required Skills</h3>

        {" ".join(
            f'<span class="badge">{x}</span>'
            for x in required
        )}
    </div>

    <div class="card">

        <h2>Best Matching Candidates</h2>

        <table>

            <tr>
                <th>Rank</th>
                <th>Candidate</th>
                <th>Experience</th>
                <th>Skill Match</th>
                <th>Final Score</th>
            </tr>

            {rows}

        </table>

    </div>

    """)


# ================= RECRUITER =================

@app.route("/recruiter")
def recruiter():

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db()

    users = conn.execute("""
        SELECT * FROM users
        WHERE role='candidate'
        ORDER BY score DESC
    """).fetchall()

    conn.close()

    rows = ""

    for rank, user in enumerate(users, 1):

        rows += f"""
        <tr>

            <td>{rank}</td>

            <td>{user["name"]}</td>

            <td>{user["email"]}</td>

            <td>{user["experience"]} yrs</td>

            <td>{user["skills"]}</td>

            <td>
                <b>{user["score"]}/100</b>
            </td>

        </tr>
        """

    return page("Recruiter Dashboard", f"""

    <h1>Recruiter Dashboard 🏢</h1>

    <div class="card">

        <h2>Candidate Ranking</h2>

        <table>

        <tr>
            <th>Rank</th>
            <th>Name</th>
            <th>Email</th>
            <th>Experience</th>
            <th>Skills</th>
            <th>Score</th>
        </tr>

        {rows}

        </table>

    </div>

    <div class="card">

        <h2>Job Matching</h2>

        <a class="btn" href="/jobs">
            Match Candidates to Jobs
        </a>

    </div>

    """)


# ================= ERROR HANDLING =================

@app.errorhandler(404)
def not_found(error):

    return page("404", """
    <div class="card">
        <h1>404</h1>
        <p>Page not found.</p>
        <a class="btn" href="/">Go Home</a>
    </div>
    """), 404


# ================= RUN =================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
