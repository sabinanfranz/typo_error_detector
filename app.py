import os
import uuid
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__, static_folder=".", static_url_path="")

# Serve the uploader HTML
@app.get("/")
def index():
    return app.send_static_file("uploader.html")

# API endpoint to process PDF
@app.post("/api/process")
def api_process():
    pdf = request.files.get("pdf")
    if not pdf:
        return jsonify({"error": "PDF 파일이 필요합니다."}), 400

    # Save uploaded PDF
    os.makedirs("pdf", exist_ok=True)
    filename = f"{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join("pdf", filename)
    pdf.save(pdf_path)

    # Build command for run.py
    cmd = ["python", "run.py", pdf_path]
    fmt = request.form.get("format", "both")
    cmd += ["--format", fmt]
    checkers = request.form.getlist("checkers")
    if "hanspell" in checkers:
        cmd.append("--hanspell")
    if "spacing" in checkers:
        cmd.append("--spacing")
    if "rule" in checkers:
        cmd.append("--rule")
    if "languagetool" in checkers:
        cmd.append("--languagetool")

    # Run detection
    subprocess.run(cmd, check=True)

    result = {}
    if fmt in ["csv", "both"]:
        result["csv"] = "/out/review.csv"
    if fmt in ["xlsx", "both"]:
        result["xlsx"] = "/out/review.xlsx"
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
