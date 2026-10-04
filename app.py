```python
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/submit-login", methods=["POST"])
def submit_login():
    email = request.form.get("email")
    password = request.form.get("password")

    if email and password:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/submit-register", methods=["POST"])
def submit_register():
    name = request.form.get("name")
    email = request.form.get("email")

    if name and email:
        return redirect(url_for("login"))

    return redirect(url_for("register"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```
