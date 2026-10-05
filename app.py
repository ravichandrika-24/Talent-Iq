import os
import re
import sqlite3
from functools import wraps

from flask import (
    Flask, request, redirect, url_for, session,
    render_template_string, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "talentiq-change-this-secret"
)

DB = "talentiq.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx"}

SKILLS = [
    "java", "python", "javascript", "html", "css",
    "react", "angular", "spring", "spring boot",
    "django", "flask", "sql", "mysql", "postgresql",
    "mongodb", "git", "github", "docker", "aws",
    "machine learning", "data analytics", "data science",
    "excel", "power bi", "c", "c++"
]


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'candidate'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            phone TEXT,
            education TEXT,
            skills TEXT,
            resume TEXT,
            resume_score INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            skills TEXT NOT NULL,
            description TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_id INTEGER,
            score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Applied'
        )
    """)

    conn.commit()

    count = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    if count == 0:
        jobs = [
            (
                "Java Full Stack Developer",
                "Product Company",
                "java,spring boot,html,css,javascript,sql",
                "Build scalable full-stack applications."
            ),
            (
                "Python Developer",
                "Technology Company",
                "python,django,flask,sql,git",
                "Develop Python backend applications."
            ),
            (
                "Data Analyst",
                "Analytics Company",
                "python,sql,excel,power bi,data analytics",
                "Analyze business data and create dashboards."
            ),
            (
                "Software Engineer",
                "Tech Company",
                "java,python,git,sql,docker",
                "Develop and maintain software products."
            )
        ]

        conn.executemany("""
            INSERT INTO jobs
            (title, company, skills, description)
            VALUES (?, ?, ?, ?)
        """, jobs)

        conn.commit()

    conn.close()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return function(*args, **kwargs)

    return wrapper


def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def extract_text(filepath):
    extension = filepath.rsplit(".", 1)[1].lower()

    if extension == "pdf":

        if PdfReader is None:
            return ""

        reader = PdfReader(filepath)

        text = []

        for page in reader.pages:
            text.append(page.extract_text() or "")

        return "\n".join(text)

    if extension == "docx":

        if Document is None:
            return ""

        document = Document(filepath)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    return ""


def analyze_resume(text):

    lower = text.lower()

    detected_skills = []

    for skill in SKILLS:
        if skill in lower:
            detected_skills.append(skill)

    email = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    phone = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )

    education = any(
        word in lower
        for word in [
            "education",
            "b.tech",
            "btech",
            "bachelor",
            "degree",
            "university"
        ]
    )

    experience = any(
        word in lower
        for word in [
            "experience",
            "internship",
            "intern",
            "worked"
        ]
    )

    projects = "project" in lower

    skills_section = "skill" in lower

    score = 0

    if email:
        score += 10

    if phone:
        score += 10

    if education:
        score += 15

    if experience:
        score += 15

    if projects:
        score += 15

    if skills_section:
        score += 10

    score += min(len(detected_skills) * 3, 25)

    score = min(score, 100)

    return {
        "score": score,
        "skills": detected_skills,
        "email": email.group(0) if email else "Not detected",
        "phone": phone.group(0) if phone else "Not detected",
        "education": education,
        "experience": experience,
        "projects": projects,
        "skills_section": skills_section
    }


def match_score(candidate_skills, job_skills):

    candidate = {
        x.strip().lower()
        for x in candidate_skills.split(",")
        if x.strip()
    }

    job = {
        x.strip().lower()
        for x in job_skills.split(",")
        if x.strip()
    }

    if not job:
        return 0

    matched = candidate.intersection(job)

    return int((len(matched) / len(job)) * 100)


BASE = """
<!DOCTYPE html>
<html>
<head>
<title>TalentIQ</title>

<style>

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    color: #222;
}

nav {
    background: #111827;
    padding: 18px;
}

nav a {
    color: white;
    text-decoration: none;
    margin-right: 20px;
    font-weight: bold;
}

.container {
    max-width: 1100px;
    margin: 40px auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 25px;
    margin: 20px 0;
    border-radius: 15px;
    box-shadow: 0 5px 20px #0001;
}

button {
    background: #635bff;
    color: white;
    border: 0;
    padding: 12px 20px;
    border-radius: 8px;
    cursor: pointer;
}

input, textarea, select {
    width: 100%;
    padding: 12px;
    margin: 8px 0 15px;
    box-sizing: border-box;
}

.score {
    font-size: 40px;
    font-weight: bold;
}

.skill {
    display: inline-block;
    padding: 7px 12px;
    margin: 5px;
    background: #eee;
    border-radius: 20px;
}

.success {
    color: green;
}

.danger {
    color: red;
}

</style>
</head>

<body>

<nav>
<a href="/">TalentIQ</a>

{% if session.get("user_id") %}
<a href="/dashboard">Dashboard</a>
<a href="/profile">Resume</a>
<a href="/jobs">Jobs</a>
<a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
<a href="/register">Register</a>
{% endif %}

</nav>

<div class="container">

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="card">{{ message }}</div>
{% endfor %}
{% endwith %}

{{ content|safe }}

</div>

</body>
</html>
"""


@app.route("/")
def home():

    content = """
    <div class="card">

    <h1>TalentIQ</h1>

    <h2>AI-Powered Talent Intelligence & Career Platform</h2>

    <p>
    Upload your resume, analyze your skills,
    calculate your resume score and discover
    suitable jobs.
    </p>

    <a href="/register">
    <button>Get Started</button>
    </a>

    </div>
    """

    return render_template_string(BASE, content=content)


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = db()

        try:

            cursor = conn.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                generate_password_hash(password)
            ))

            user_id = cursor.lastrowid

            conn.execute("""
                INSERT INTO profiles (user_id)
                VALUES (?)
            """, (user_id,))

            conn.commit()

            flash("Registration successful. Please login.")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("Email already registered.")

        finally:
            conn.close()

    content = """
    <div class="card">

    <h2>Create TalentIQ Account</h2>

    <form method="POST">

    <input
        name="name"
        placeholder="Full Name"
        required
    >

    <input
        type="email"
        name="email"
        placeholder="Email"
        required
    >

    <input
        type="password"
        name="password"
        placeholder="Password"
        required
    >

    <button>Create Account</button>

    </form>

    </div>
    """

    return render_template_string(BASE, content=content)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    content = """
    <div class="card">

    <h2>Login</h2>

    <form method="POST">

    <input
        type="email"
        name="email"
        placeholder="Email"
        required
    >

    <input
        type="password"
        name="password"
        placeholder="Password"
        required
    >

    <button>Login</button>

    </form>

    </div>
    """

    return render_template_string(BASE, content=content)


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    conn = db()

    profile = conn.execute("""
        SELECT * FROM profiles
        WHERE user_id=?
    """, (session["user_id"],)).fetchone()

    if request.method == "POST":

        phone = request.form.get("phone", "")
        education = request.form.get("education", "")
        skills = request.form.get("skills", "")

        resume = request.files.get("resume")

        resume_name = profile["resume"]
        resume_score = profile["resume_score"]

        if resume and resume.filename:

            if not allowed_file(resume.filename):

                flash("Only PDF and DOCX resumes are allowed.")

                conn.close()

                return redirect(url_for("profile"))

            filename = secure_filename(resume.filename)

            filename = (
                str(session["user_id"])
                + "_"
                + filename
            )

            filepath = os.path.join(
                UPLOAD_DIR,
                filename
            )

            resume.save(filepath)

            text = extract_text(filepath)

            if not text.strip():

                flash(
                    "Resume could not be read. "
                    "Please upload a text-based PDF or DOCX."
                )

            else:

                analysis = analyze_resume(text)

                detected = ",".join(
                    analysis["skills"]
                )

                skills = detected or skills

                resume_score = analysis["score"]

                resume_name = filename

                session["resume_analysis"] = analysis

                flash(
                    "Resume analyzed successfully! "
                    f"Score: {resume_score}%"
                )

        conn.execute("""
            UPDATE profiles
            SET phone=?,
                education=?,
                skills=?,
                resume=?,
                resume_score=?
            WHERE user_id=?
        """, (
            phone,
            education,
            skills,
            resume_name,
            resume_score,
            session["user_id"]
        ))

        conn.commit()

    profile = conn.execute("""
        SELECT * FROM profiles
        WHERE user_id=?
    """, (session["user_id"],)).fetchone()

    conn.close()

    analysis = session.get("resume_analysis")

    analysis_html = ""

    if analysis:

        skills_html = ""

        for skill in analysis["skills"]:
            skills_html += (
                f'<span class="skill">{skill}</span>'
            )

        analysis_html = f"""
        <div class="card">

        <h2>Resume Analysis</h2>

        <div class="score">
        {analysis["score"]}%
        </div>

        <p>Resume Score</p>

        <h3>Detected Skills</h3>

        {skills_html or "No skills detected"}

        <h3>Contact</h3>

        <p>Email: {analysis["email"]}</p>
        <p>Phone: {analysis["phone"]}</p>

        <h3>Resume Sections</h3>

        <p>
        Education:
        {"✅ Found" if analysis["education"] else "❌ Missing"}
        </p>

        <p>
        Experience:
        {"✅ Found" if analysis["experience"] else "❌ Missing"}
        </p>

        <p>
        Projects:
        {"✅ Found" if analysis["projects"] else "❌ Missing"}
        </p>

        <p>
        Skills:
        {"✅ Found" if analysis["skills_section"] else "❌ Missing"}
        </p>

        </div>
        """

    content = f"""
    <div class="card">

    <h2>My Resume</h2>

    <form method="POST" enctype="multipart/form-data">

    <label>Phone</label>

    <input
        name="phone"
        value="{profile["phone"] or ""}"
    >

    <label>Education</label>

    <input
        name="education"
        value="{profile["education"] or ""}"
    >

    <label>Skills</label>

    <input
        name="skills"
        value="{profile["skills"] or ""}"
        placeholder="Java, Python, SQL"
    >

    <label>Upload Resume</label>

    <input
        type="file"
        name="resume"
        accept=".pdf,.docx"
        required
    >

    <button>
    Upload & Analyze Resume
    </button>

    </form>

    </div>

    {analysis_html}
    """

    return render_template_string(BASE, content=content)


@app.route("/jobs")
@login_required
def jobs():

    conn = db()

    jobs = conn.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    profile = conn.execute("""
        SELECT * FROM profiles
        WHERE user_id=?
    """, (session["user_id"],)).fetchone()

    conn.close()

    cards = ""

    for job in jobs:

        score = match_score(
            profile["skills"] or "",
            job["skills"]
        )

        cards += f"""
        <div class="card">

        <h2>{job["title"]}</h2>

        <h3>{job["company"]}</h3>

        <p>{job["description"]}</p>

        <p>
        Required Skills:
        {job["skills"]}
        </p>

        <h2>{score}% Match</h2>

        <a href="/apply/{job["id"]}">
        <button>Apply Now</button>
        </a>

        </div>
        """

    content = f"""
    <h1>Recommended Jobs</h1>

    {cards}
    """

    return render_template_string(BASE, content=content)


@app.route("/apply/<int:job_id>")
@login_required
def apply(job_id):

    conn = db()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?",
        (job_id,)
    ).fetchone()

    profile = conn.execute("""
        SELECT * FROM profiles
        WHERE user_id=?
    """, (session["user_id"],)).fetchone()

    if not job:
        conn.close()
        return "Job not found", 404

    score = match_score(
        profile["skills"] or "",
        job["skills"]
    )

    existing = conn.execute("""
        SELECT * FROM applications
        WHERE user_id=? AND job_id=?
    """, (
        session["user_id"],
        job_id
    )).fetchone()

    if not existing:

        conn.execute("""
            INSERT INTO applications
            (user_id, job_id, score)
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            job_id,
            score
        ))

        conn.commit()

        flash(
            f"Application submitted! "
            f"Job match: {score}%"
        )

    else:

        flash("You already applied for this job.")

    conn.close()

    return redirect(url_for("jobs"))


@app.route("/dashboard")
@login_required
def dashboard():

    conn = db()

    profile = conn.execute("""
        SELECT * FROM profiles
        WHERE user_id=?
    """, (session["user_id"],)).fetchone()

    applications = conn.execute("""
        SELECT applications.*, jobs.title, jobs.company
        FROM applications
        JOIN jobs ON jobs.id=applications.job_id
        WHERE applications.user_id=?
        ORDER BY applications.id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    application_html = ""

    for application in applications:

        application_html += f"""
        <div class="card">

        <h3>{application["title"]}</h3>

        <p>{application["company"]}</p>

        <p>
        Match Score:
        <b>{application["score"]}%</b>
        </p>

        <p>
        Status:
        {application["status"]}
        </p>

        </div>
        """

    content = f"""
    <div class="card">

    <h1>Welcome, {session["name"]}</h1>

    <h2>
    Resume Score:
    {profile["resume_score"] or 0}%
    </h2>

    <p>
    Skills:
    {profile["skills"] or "Upload your resume"}
    </p>

    </div>

    <h2>My Applications</h2>

    {application_html or
     '<div class="card">No applications yet.</div>'}
    """

    return render_template_string(BASE, content=content)


@app.route("/health")
def health():

    return {
        "status": "ok",
        "service": "TalentIQ",
        "resume_analysis": True,
        "job_matching": True
    }


init_db()


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
