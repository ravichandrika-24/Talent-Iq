import os
import re
import sqlite3
from functools import wraps

from flask import Flask, request, redirect, url_for, session, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from PyPDF2 import PdfReader
from docx import Document


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "talentiq-production-secret"
)

DB = "talentiq.db"
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx"}

SKILLS = [
    "java",
    "python",
    "javascript",
    "html",
    "css",
    "react",
    "angular",
    "spring",
    "spring boot",
    "django",
    "flask",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "git",
    "github",
    "docker",
    "aws",
    "machine learning",
    "data analytics",
    "data science",
    "excel",
    "power bi",
    "c",
    "c++"
]


# =========================
# DATABASE
# =========================

def get_db():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():

    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.execute("""
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

    connection.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            skills TEXT NOT NULL,
            description TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_id INTEGER,
            score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Applied'
        )
    """)

    count = connection.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    if count == 0:

        jobs = [

            (
                "Java Full Stack Developer",
                "Product Company",
                "java,spring boot,html,css,javascript,sql",
                "Build modern full-stack applications."
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
                "Analyze data and create dashboards."
            ),

            (
                "Software Engineer",
                "Technology Company",
                "java,python,git,sql,docker",
                "Develop scalable software products."
            )
        ]

        connection.executemany("""
            INSERT INTO jobs
            (title, company, skills, description)
            VALUES (?, ?, ?, ?)
        """, jobs)

    connection.commit()
    connection.close()


# =========================
# LOGIN
# =========================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# =========================
# RESUME
# =========================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def extract_resume_text(filepath):

    extension = filepath.rsplit(".", 1)[1].lower()

    if extension == "pdf":

        reader = PdfReader(filepath)

        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text

    if extension == "docx":

        document = Document(filepath)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    return ""


def analyze_resume(text):

    lower_text = text.lower()

    detected_skills = []

    for skill in SKILLS:

        if skill.lower() in lower_text:
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
        item in lower_text
        for item in [
            "education",
            "b.tech",
            "btech",
            "bachelor",
            "degree",
            "university"
        ]
    )

    experience = any(
        item in lower_text
        for item in [
            "experience",
            "internship",
            "intern",
            "worked"
        ]
    )

    projects = "project" in lower_text

    skills_section = (
        "skill" in lower_text
    )

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

    score += min(
        len(detected_skills) * 3,
        25
    )

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


# =========================
# JOB MATCHING
# =========================

def match_score(candidate_skills, job_skills):

    candidate = {
        skill.strip().lower()
        for skill in candidate_skills.split(",")
        if skill.strip()
    }

    required = {
        skill.strip().lower()
        for skill in job_skills.split(",")
        if skill.strip()
    }

    if not required:
        return 0

    matched = candidate.intersection(required)

    return int(
        len(matched) / len(required) * 100
    )


# =========================
# DESIGN
# =========================

BASE_HTML = """

<!DOCTYPE html>

<html>

<head>

<title>TalentIQ</title>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
    Arial,
    Helvetica,
    sans-serif;

    background:
    #f5f7fb;

    color:
    #111827;
}

nav {

    background:
    #111827;

    padding:
    18px;

}

nav a {

    color:
    white;

    text-decoration:
    none;

    margin-right:
    22px;

    font-weight:
    bold;

}

.container {

    max-width:
    1100px;

    margin:
    35px auto;

    padding:
    20px;

}

.card {

    background:
    white;

    border-radius:
    16px;

    padding:
    25px;

    margin-bottom:
    20px;

    box-shadow:
    0 8px 25px
    rgba(0,0,0,.08);

}

button {

    background:
    #635bff;

    color:
    white;

    border:
    none;

    border-radius:
    8px;

    padding:
    12px 20px;

    cursor:
    pointer;

    font-weight:
    bold;

}

button:hover {

    opacity:
    .9;

}

input,
textarea {

    width:
    100%;

    padding:
    13px;

    margin:
    8px 0 16px;

    border:
    1px solid #ddd;

    border-radius:
    8px;

}

.score {

    font-size:
    45px;

    font-weight:
    bold;

    color:
    #635bff;

}

.skill {

    display:
    inline-block;

    background:
    #eef2ff;

    padding:
    8px 13px;

    border-radius:
    20px;

    margin:
    4px;

}

.match {

    font-size:
    25px;

    font-weight:
    bold;

}

.success {

    color:
    green;

}

.danger {

    color:
    red;

}

.hero {

    text-align:
    center;

    padding:
    70px 20px;

}

</style>

</head>

<body>


<nav>

<a href="/">
TalentIQ
</a>

{% if session.get("user_id") %}

<a href="/dashboard">
Dashboard
</a>

<a href="/profile">
My Resume
</a>

<a href="/jobs">
Jobs
</a>

<a href="/logout">
Logout
</a>

{% else %}

<a href="/login">
Login
</a>

<a href="/register">
Register
</a>

{% endif %}

</nav>


<div class="container">

{% with messages =
get_flashed_messages() %}

{% for message in messages %}

<div class="card">

{{ message }}

</div>

{% endfor %}

{% endwith %}


{{ content|safe }}


</div>

</body>

</html>

"""


# =========================
# HOME
# =========================

@app.route("/")
def home():

    content = """

    <div class="card hero">

        <h1>
        TalentIQ
        </h1>

        <h2>
        Intelligent Recruitment &
        Candidate Analytics
        </h2>

        <p>
        Upload your resume.
        Analyze your skills.
        Get a resume score.
        Find matching jobs.
        </p>

        <br>

        <a href="/register">

            <button>
            Get Started
            </button>

        </a>

    </div>

    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# =========================
# REGISTER
# =========================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        connection = get_db()

        try:

            cursor = connection.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    generate_password_hash(password)
                )
            )

            user_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO profiles
                (user_id)
                VALUES (?)
                """,
                (user_id,)
            )

            connection.commit()

            flash(
                "Account created successfully."
            )

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            flash(
                "Email already registered."
            )

        finally:

            connection.close()

    content = """

    <div class="card">

    <h2>
    Create TalentIQ Account
    </h2>

    <form method="POST">

    <input
    name="name"
    placeholder="Full Name"
    required>

    <input
    type="email"
    name="email"
    placeholder="Email"
    required>

    <input
    type="password"
    name="password"
    placeholder="Password"
    required>

    <button>
    Register
    </button>

    </form>

    </div>

    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email=?
            """,
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["name"] = user["name"]

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password."
        )

    content = """

    <div class="card">

    <h2>
    Login
    </h2>

    <form method="POST">

    <input
    type="email"
    name="email"
    placeholder="Email"
    required>

    <input
    type="password"
    name="password"
    placeholder="Password"
    required>

    <button>
    Login
    </button>

    </form>

    </div>

    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================
# PROFILE / RESUME
# =========================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
def profile():

    connection = get_db()

    profile = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchone()

    analysis = None

    if request.method == "POST":

        phone = request.form.get(
            "phone",
            ""
        )

        education = request.form.get(
            "education",
            ""
        )

        skills = request.form.get(
            "skills",
            ""
        )

        resume = request.files.get(
            "resume"
        )

        resume_name = profile["resume"]

        resume_score = profile["resume_score"] or 0

        if resume and resume.filename:

            if not allowed_file(
                resume.filename
            ):

                flash(
                    "Please upload only PDF or DOCX."
                )

                connection.close()

                return redirect(
                    url_for("profile")
                )

            filename = secure_filename(
                resume.filename
            )

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

            try:

                resume_text = (
                    extract_resume_text(
                        filepath
                    )
                )

                if not resume_text.strip():

                    flash(
                        "Resume has no readable text."
                    )

                else:

                    analysis = analyze_resume(
                        resume_text
                    )

                    detected_skills = (
                        analysis["skills"]
                    )

                    if detected_skills:

                        skills = ",".join(
                            detected_skills
                        )

                    resume_score = (
                        analysis["score"]
                    )

                    resume_name = filename

                    session[
                        "resume_analysis"
                    ] = analysis

                    flash(
                        "Resume analyzed successfully! "
                        f"Score: {resume_score}%"
                    )

            except Exception:

                flash(
                    "Could not analyze this resume."
                )

        connection.execute(
            """
            UPDATE profiles

            SET
            phone=?,
            education=?,
            skills=?,
            resume=?,
            resume_score=?

            WHERE user_id=?
            """,
            (
                phone,
                education,
                skills,
                resume_name,
                resume_score,
                session["user_id"]
            )
        )

        connection.commit()

    profile = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchone()

    connection.close()

    analysis = session.get(
        "resume_analysis"
    )

    analysis_html = ""

    if analysis:

        skill_html = ""

        for skill in analysis["skills"]:

            skill_html += (
                f'<span class="skill">'
                f'{skill}'
                f'</span>'
            )

        analysis_html = f"""

        <div class="card">

        <h2>
        Resume Analysis
        </h2>

        <div class="score">

        {analysis["score"]}%

        </div>

        <p>
        Resume Score
        </p>

        <h3>
        Detected Skills
        </h3>

        {skill_html or "No skills detected"}

        <h3>
        Contact Information
        </h3>

        <p>
        Email:
        {analysis["email"]}
        </p>

        <p>
        Phone:
        {analysis["phone"]}
        </p>

        <h3>
        Resume Sections
        </h3>

        <p>
        Education:
        {"✅ Found"
        if analysis["education"]
        else "❌ Missing"}
        </p>

        <p>
        Experience:
        {"✅ Found"
        if analysis["experience"]
        else "❌ Missing"}
        </p>

        <p>
        Projects:
        {"✅ Found"
        if analysis["projects"]
        else "❌ Missing"}
        </p>

        <p>
        Skills:
        {"✅ Found"
        if analysis["skills_section"]
        else "❌ Missing"}
        </p>

        </div>

        """

    content = f"""

    <div class="card">

    <h2>
    My Resume
    </h2>

    <form
    method="POST"
    enctype="multipart/form-data">

    <label>
    Phone
    </label>

    <input
    name="phone"
    value="{profile["phone"] or ""}">

    <label>
    Education
    </label>

    <input
    name="education"
    value="{profile["education"] or ""}">

    <label>
    Skills
    </label>

    <input
    name="skills"
    value="{profile["skills"] or ""}"
    placeholder="Java, Python, SQL">

    <label>
    Resume
    </label>

    <input
    type="file"
    name="resume"
    accept=".pdf,.docx"
    required>

    <button>
    Upload & Analyze
    </button>

    </form>

    </div>

    {analysis_html}

    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# =========================
# JOBS
# =========================

@app.route("/jobs")
@login_required
def jobs():

    connection = get_db()

    jobs_list = connection.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    profile = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchone()

    connection.close()

    cards = ""

    for job in jobs_list:

        score = match_score(
            profile["skills"] or "",
            job["skills"]
        )

        cards += f"""

        <div class="card">

        <h2>
        {job["title"]}
        </h2>

        <h3>
        {job["company"]}
        </h3>

        <p>
        {job["description"]}
        </p>

        <p>
        Required:
        {job["skills"]}
        </p>

        <div class="match">
        {score}% Match
        </div>

        <br>

        <a href="/apply/{job["id"]}">

        <button>
        Apply Now
        </button>

        </a>

        </div>

        """

    content = f"""

    <h1>
    Recommended Jobs
    </h1>

    {cards}

    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# =========================
# APPLY
# =========================

@app.route("/apply/<int:job_id>")
@login_required
def apply(job_id):

    connection = get_db()

    job = connection.execute(
        """
        SELECT *
        FROM jobs
        WHERE id=?
        """,
        (job_id,)
    ).fetchone()

    profile = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchone()

    if not job:

        connection.close()

        return "Job not found", 404

    score = match_score(
        profile["skills"] or "",
        job["skills"]
    )

    existing = connection.execute(
        """
        SELECT *
        FROM applications
        WHERE user_id=?
        AND job_id=?
        """,
        (
            session["user_id"],
            job_id
        )
    ).fetchone()

    if not existing:

        connection.execute(
            """
            INSERT INTO applications
            (user_id, job_id, score)
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                job_id,
                score
            )
        )

        connection.commit()

        flash(
            f"Application submitted! "
            f"Match Score: {score}%"
        )

    else:

        flash(
            "You already applied for this job."
        )

    connection.close()

    return redirect(
        url_for("jobs")
    )


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
@login_required
def dashboard():

    connection = get_db()

    profile = connection.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchone()

    applications = connection.execute(
        """
        SELECT
        applications.*,
        jobs.title,
        jobs.company

        FROM applications

        JOIN jobs
        ON jobs.id=applications.job_id

        WHERE applications.user_id=?

        ORDER BY applications.id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    applications_html = ""

    for application in applications:

        applications_html += f"""

        <div class="card">

        <h3>
        {application["title"]}
        </h3>

        <p>
        {application["company"]}
        </p>

        <p>
        Match:
        <b>
        {application["score"]}%
        </b>
        </p>

        <p>
        Status:
        {application["status"]}
        </p>

        </div>

        """

    content = f"""

    <div class="card">

    <h1>
    Welcome,
    {session["name"]}
    </h1>

    <h2>
    Resume Score:
    {profile["resume_score"] or 0}%
    </h2>

    <p>
    Skills:
    {profile["skills"] or "Upload your resume"}
    </p>

    </div>


    <h2>
    My Applications
    </h2>

    {applications_html or
    '<div class="card">No applications yet.</div>'}

    """

    return render_template_string(
        BASE_HTML,
        content=content
    )


# =========================
# HEALTH CHECK
# =========================

@app.route("/health")
def health():

    return {

        "status": "ok",

        "service": "TalentIQ",

        "resume_upload": True,

        "resume_analysis": True,

        "pdf_support": True,

        "docx_support": True,

        "job_matching": True

    }


# =========================
# START
# =========================

init_db()


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
