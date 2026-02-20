from flask import Flask, render_template, request, redirect, url_for, session
from .api.turss_info_api import info_bp
from .api.chat_api import chat_bp
from .api.login_api import login_bp
from .config import SK

app = Flask(__name__)
app.secret_key = SK or "dev-secret-key-change-in-production"

app.register_blueprint(info_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(login_bp)

@app.before_request
def require_login():
    if request.path.startswith('/static/') or request.path == '/login' or request.path == '/api/login' or request.path == '/api/logout':
        return
    if 'logged_in' not in session or not session.get('logged_in'):
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/truss-info')
def truss_info():
    return render_template("truss_info.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/login")
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template("login.html")

if __name__== "__main__":
    app.run(debug=True)