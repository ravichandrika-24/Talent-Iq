from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3, os, re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "talentiq-production-secret-change-me")

DB = "talentiq.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TalentIQ</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:#f5f7fb;color:#172033}
nav{background:#111827;color:white;padding:18px 6%;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:25px;font-weight:bold;color:#7c5cff}
nav a{color:white;text-decoration:none;margin-left:20px}
.container{max-width:1100px;margin:35px auto;padding:0 20px}
.hero{background:linear-gradient(135deg,#17132f,#635bff);color:white;padding:55px 35px;border-radius:20px;margin-bottom:30px}
.hero h1{font-size:42px;margin:0 0 15px}
.card{background:white;padding:25px;border-radius:16px;margin:18px 0;box-shadow:0 5px 25px #0000000d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px}
input,textarea,select{width:100%;padding:13px;margin:8px 0 15px;border:1px solid #ddd;border-radius:9px}
button,.btn{background:#635bff;color:white;border:0;padding:12px 20px;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-block}
button:hover,.btn:hover{background:#4d46d9}
.score{font-size:25px;font-weight:bold;color:#635bff}
.badge{padding:5px 10px;background:#eee;border-radius:20px}
.flash{padding:12px;background:#fff3cd;border-radius:8px;margin:10px 0}
small{color:#667085}
</style>
</head>
<body>
<nav>
<div class="logo">🧠 TalentIQ</div>
<div>
<a href="/">Home</a>
{% if session.get('user_id') %}
<a href="/dashboard">Dashboard</a>
<a href="/jobs">Jobs</a>
<a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
<a href="/register">Register</a>
{% endif %}
</div>
</nav>

<div class="container">
{% with messages=get_flashed_messages() %}
{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}
{% endwith %}
{{content|safe}}
</div>
</body>
</html>
"""

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'candidate'
    );

    CREATE TABLE IF NOT EXISTS profiles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        skills TEXT DEFAULT '',
        experience TEXT DEFAULT '',
        education TEXT DEFAULT '',
        resume TEXT DEFAULT '',
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recruiter_id INTEGER,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        description TEXT,
        skills TEXT,
        location TEXT,
        salary TEXT,
        FOREIGN KEY(recruiter_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        candidate_id INTEGER,
        status TEXT DEFAULT 'Applied',
        score INTEGER DEFAULT 0,
        UNIQUE(job_id,candidate_id),
        FOREIGN KEY(job_id) REFERENCES jobs(id),
        FOREIGN KEY(candidate_id) REFERENCES users(id)
    );
    """)
    c.commit()
    c.close()

def layout(content):
    return render_template_string(HTML, content=content)

def match_score(candidate_skills, job_skills):
    a = set(re.findall(r"[a-zA-Z0-9+#.]+", (candidate_skills or "").lower()))
    b = set(re.findall(r"[a-zA-Z0-9+#.]+", (job_skills or "").lower()))
    if not b:
        return 0
    return round(len(a & b) / len(b) * 100)

@app.route("/")
def home():
    return layout("""
    <div class="hero">
        <h1>TalentIQ</h1>
        <p>Intelligent Recruitment & Career Intelligence Platform</p>
        <p>Connect candidates with the right opportunities using skill-based matching.</p>
        <a class="btn" href="/register">Get Started</a>
        <a class="btn" href="/jobs">Explore Jobs</a>
    </div>

    <div class="grid">
      <div class="card"><h2>🎯 Smart Matching</h2><p>Automatically calculate candidate-job compatibility.</p></div>
      <div class="card"><h2>📄 Resume Management</h2><p>Upload and manage candidate resumes.</p></div>
      <div class="card"><h2>💼 Recruitment</h2><p>Recruiters can post jobs and manage applications.</p></div>
      <div class="card"><h2>📊 Analytics</h2><p>View applications, rankings and hiring data.</p></div>
    </div>
    """)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name=request.form["name"].strip()
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        role=request.form["role"]

        try:
            c=db()
            c.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (name,email,generate_password_hash(password),role)
            )
            c.commit()
            c.close()
            flash("Registration successful. Please login.")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Email already registered.")

    return layout("""
    <div class="card">
    <h1>Create TalentIQ Account</h1>
    <form method="post">
      <input name="name" placeholder="Full name" required>
      <input name="email" type="email" placeholder="Email" required>
      <input name="password" type="password" placeholder="Password" required>
      <select name="role">
        <option value="candidate">Candidate</option>
        <option value="recruiter">Recruiter</option>
      </select>
      <button>Register</button>
    </form>
    </div>
    """)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        password=request.form["password"]

        c=db()
        u=c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        c.close()

        if u and check_password_hash(u["password"],password):
            session["user_id"]=u["id"]
            session["name"]=u["name"]
            session["role"]=u["role"]
            return redirect("/dashboard")

        flash("Invalid email or password.")

    return layout("""
    <div class="card">
    <h1>Login</h1>
    <form method="post">
      <input name="email" type="email" placeholder="Email" required>
      <input name="password" type="password" placeholder="Password" required>
      <button>Login</button>
    </form>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/login")

    uid=session["user_id"]

    if session["role"]=="candidate":
        c=db()
        p=c.execute("SELECT * FROM profiles WHERE user_id=?", (uid,)).fetchone()
        apps=c.execute("""
        SELECT applications.*,jobs.title,jobs.company
        FROM applications JOIN jobs ON jobs.id=applications.job_id
        WHERE candidate_id=?
        ORDER BY applications.id DESC
        """,(uid,)).fetchall()
        jobs=c.execute("SELECT * FROM jobs").fetchall()
        c.close()

        skills=p["skills"] if p else ""

        job_cards=""
        for j in jobs:
            score=match_score(skills,j["skills"])
            job_cards+=f"""
            <div class="card">
            <h3>{j["title"]}</h3>
            <b>{j["company"]}</b><br>
            <small>{j["location"]} | {j["salary"]}</small>
            <p>{j["description"] or ""}</p>
            <span class="score">{score}% Match</span><br><br>
            <a class="btn" href="/apply/{j["id"]}">Apply</a>
            </div>
            """

        apps_html="".join(
            f"<div class='card'><b>{a['title']}</b> - {a['company']}<br>"
            f"Match: {a['score']}% | Status: <span class='badge'>{a['status']}</span></div>"
            for a in apps
        )

        return layout(f"""
        <h1>Welcome, {session["name"]} 👋</h1>

        <div class="card">
        <h2>Your Candidate Profile</h2>
        <form method="post" action="/profile" enctype="multipart/form-data">
          <input name="skills" value="{skills}" placeholder="Skills: Python, Java, SQL, React">
          <input name="experience" value="{p['experience'] if p else ''}" placeholder="Experience">
          <input name="education" value="{p['education'] if p else ''}" placeholder="Education">
          <input type="file" name="resume">
          <button>Save Profile</button>
        </form>
        </div>

        <h2>Recommended Jobs</h2>
        {job_cards or "<p>No jobs available yet.</p>"}

        <h2>My Applications</h2>
        {apps_html or "<p>No applications yet.</p>"}
        """)

    c=db()
    jobs=c.execute(
        "SELECT * FROM jobs WHERE recruiter_id=? ORDER BY id DESC",
        (uid,)
    ).fetchall()

    apps=c.execute("""
    SELECT applications.*,users.name,users.email,jobs.title
    FROM applications
    JOIN users ON users.id=applications.candidate_id
    JOIN jobs ON jobs.id=applications.job_id
    WHERE jobs.recruiter_id=?
    ORDER BY applications.score DESC
    """,(uid,)).fetchall()

    c.close()

    jobs_html="".join(
        f"<div class='card'><h3>{j['title']}</h3>"
        f"<b>{j['company']}</b><p>{j['description'] or ''}</p>"
        f"<small>Required skills: {j['skills']}</small></div>"
        for j in jobs
    )

    apps_html="".join(
        f"""
        <div class="card">
        <h3>{a['name']} → {a['title']}</h3>
        <p>{a['email']}</p>
        <div class="score">{a['score']}% Match</div>
        <p>Status: {a['status']}</p>
        <a class="btn" href="/status/{a['id']}/Shortlisted">Shortlist</a>
        <a class="btn" href="/status/{a['id']}/Interview">Interview</a>
        <a class="btn" href="/status/{a['id']}/Rejected">Reject</a>
        </div>
        """
        for a in apps
    )

    return layout(f"""
    <h1>Recruiter Dashboard</h1>

    <div class="grid">
      <div class="card"><h2>{len(jobs)}</h2><p>Jobs Posted</p></div>
      <div class="card"><h2>{len(apps)}</h2><p>Applications</p></div>
    </div>

    <div class="card">
    <h2>Post a Job</h2>
    <form method="post" action="/jobs/new">
      <input name="title" placeholder="Job title" required>
      <input name="company" placeholder="Company" required>
      <input name="skills" placeholder="Required skills: Python, Java, SQL" required>
      <input name="location" placeholder="Location / Remote">
      <input name="salary" placeholder="Salary">
      <textarea name="description" placeholder="Job description"></textarea>
      <button>Publish Job</button>
    </form>
    </div>

    <h2>Your Jobs</h2>{jobs_html}

    <h2>Candidate Applications & Ranking</h2>
    {apps_html or "<p>No applications yet.</p>"}
    """)

@app.route("/profile", methods=["POST"])
def profile():
    if not session.get("user_id"):
        return redirect("/login")

    uid=session["user_id"]
    skills=request.form.get("skills","")
    experience=request.form.get("experience","")
    education=request.form.get("education","")
    resume=""

    f=request.files.get("resume")
    if f and f.filename:
        resume=secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_DIR,resume))

    c=db()
    old=c.execute("SELECT * FROM profiles WHERE user_id=?",(uid,)).fetchone()

    if old:
        if not resume:
            resume=old["resume"]
        c.execute("""
        UPDATE profiles SET skills=?,experience=?,education=?,resume=?
        WHERE user_id=?
        """,(skills,experience,education,resume,uid))
    else:
        c.execute("""
        INSERT INTO profiles(user_id,skills,experience,education,resume)
        VALUES(?,?,?,?,?)
        """,(uid,skills,experience,education,resume))

    c.commit()
    c.close()
    flash("Profile updated successfully.")
    return redirect("/dashboard")

@app.route("/jobs")
def jobs():
    c=db()
    jobs=c.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    c.close()

    cards="".join(
        f"""
        <div class="card">
        <h2>{j['title']}</h2>
        <b>{j['company']}</b>
        <p>{j['description'] or ''}</p>
        <p>Skills: <b>{j['skills']}</b></p>
        <p>📍 {j['location']} | 💰 {j['salary']}</p>
        <a class="btn" href="/apply/{j['id']}">Apply Now</a>
        </div>
        """
        for j in jobs
    )

    return layout(f"<h1>Available Jobs</h1>{cards or '<p>No jobs posted yet.</p>'}")

@app.route("/jobs/new", methods=["POST"])
def new_job():
    if session.get("role")!="recruiter":
        return redirect("/login")

    c=db()
    c.execute("""
    INSERT INTO jobs(recruiter_id,title,company,description,skills,location,salary)
    VALUES(?,?,?,?,?,?,?)
    """,(
        session["user_id"],
        request.form["title"],
        request.form["company"],
        request.form.get("description",""),
        request.form["skills"],
        request.form.get("location",""),
        request.form.get("salary","")
    ))
    c.commit()
    c.close()

    flash("Job published successfully.")
    return redirect("/dashboard")

@app.route("/apply/<int:job_id>")
def apply(job_id):
    if session.get("role")!="candidate":
        flash("Please login as a candidate to apply.")
        return redirect("/login")

    uid=session["user_id"]

    c=db()
    p=c.execute("SELECT * FROM profiles WHERE user_id=?",(uid,)).fetchone()
    job=c.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()

    if not job:
        c.close()
        return "Job not found",404

    skills=p["skills"] if p else ""
    score=match_score(skills,job["skills"])

    try:
        c.execute("""
        INSERT INTO applications(job_id,candidate_id,status,score)
        VALUES(?,?,?,?)
        """,(job_id,uid,"Applied",score))
        c.commit()
        flash(f"Application submitted! Match score: {score}%")
    except sqlite3.IntegrityError:
        flash("You already applied for this job.")

    c.close()
    return redirect("/dashboard")

@app.route("/status/<int:application_id>/<status>")
def status(application_id,status):
    if session.get("role")!="recruiter":
        return redirect("/login")

    allowed=["Applied","Shortlisted","Interview","Selected","Rejected"]

    if status not in allowed:
        return "Invalid status",400

    c=db()
    c.execute(
        "UPDATE applications SET status=? WHERE id=?",
        (status,application_id)
    )
    c.commit()
    c.close()

    return redirect("/dashboard")

@app.route("/health")
def health():
    return {"status":"online","service":"TalentIQ"}

init_db()

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port,debug=False)
