```python
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/login")
def login():
    return send_from_directory(".", "login.html")

@app.route("/register")
def register():
    return send_from_directory(".", "register.html")

@app.route("/dashboard")
def dashboard():
    return send_from_directory(".", "dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
```
