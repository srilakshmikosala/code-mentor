from flask import Flask, request, jsonify, render_template
from main import analyze_code

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")

    if not code:
        return jsonify({
            "error": "No code provided"
        }), 400

    result = analyze_code(code)

    return jsonify({
        "message": "Analysis completed successfully!",
        "result": result
    })


if __name__ == "__main__":
    app.run(debug=True)