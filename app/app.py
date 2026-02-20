from flask import Flask, render_template
from .api.turss_info_api import info_bp
from .api.chat_api import chat_bp


app = Flask(__name__)

app.register_blueprint(info_bp)
app.register_blueprint(chat_bp)

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
    return render_template("login.html")


if __name__== "__main__":
    app.run(debug=True)