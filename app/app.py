from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/truss-info')
def truss_info():
    return "in truss info page"

@app.route("/chat")
def chat():
    pass

if __name__== "__main__":
    app.run(debug=True)