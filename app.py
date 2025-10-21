from flask import Flask, render_template, request
# from app.pairing import generate_pairing

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    result = None
    return render_template("shot.html", result=result)
