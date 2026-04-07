import os
import joblib
import pandas as pd
import PyPDF2
import pytesseract
from PIL import Image
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))
from features import extract_features, parse_report

# Auto-configure Tesseract path for Windows environments (Local testing check)
if sys.platform == 'win32':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe\tesseract.exe'
app = Flask(__name__)
CORS(app)  # This allows Lovable or any external React app to talk to this API

current_dir = os.path.dirname(__file__)
model_path = os.path.join(current_dir, "..", "model", "hybrid_model.pkl")
metadata_path = os.path.join(current_dir, "..", "model", "model_metadata.pkl")

# Load globally
if os.path.exists(model_path) and os.path.exists(metadata_path):
    model = joblib.load(model_path)
    assets = joblib.load(metadata_path)
    feature_columns = assets["feature_columns"]
else:
    model, feature_columns = None, None


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    # Ensure frontend always receives JSON, not Flask HTML debug pages.
    return jsonify({"error": f"Server error: {str(exc)}"}), 500

def extract_text_from_pdf(file_stream):
    reader = PyPDF2.PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def rule_score(features):
    score = 0
    reasons = []

    if features["age_valid"] == 0:
        score += 2
        reasons.append("Age is missing or outside valid range")

    if features["has_doctor"] == 0:
        score += 2
        reasons.append("Doctor information is missing")

    if features["has_hospital"] == 0:
        score += 1
        reasons.append("Hospital/clinic information is missing")

    if features["dose_pattern_count"] == 0 and features["medicine_count"] > 0:
        score += 1
        reasons.append("Dosage pattern is missing or malformed")

    if features["dosage_extreme_flag"] == 1:
        score += 2
        reasons.append("Extreme dosage detected")

    if features["unknown_tokens_ratio"] > 0.08:
        score += 1
        reasons.append("Report contains suspicious placeholder tokens")

    return score, reasons

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/authenticate", methods=["POST"])
def authenticate():
    if model is None:
        return jsonify({"error": "Model assets not found on server. Run training first."}), 500
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    report_text = ""
    try:
        filename_lower = file.filename.lower()
        if filename_lower.endswith('.pdf'):
            report_text = extract_text_from_pdf(file)
        elif filename_lower.endswith('.txt'):
            report_text = file.read().decode("utf-8")
        elif filename_lower.endswith(('.png', '.jpg', '.jpeg')):
            try:
                img = Image.open(file)
                report_text = pytesseract.image_to_string(img)
            except pytesseract.TesseractNotFoundError:
                return jsonify({"error": "Tesseract OCR engine is not installed on this server. Image extraction failed."}), 500
            except Exception as img_e:
                return jsonify({"error": f"Bad Image File: {str(img_e)}"}), 400
        else:
            return jsonify({"error": "Unsupported file format. Please upload PDF, TXT, or Image."}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to extract text: {str(e)}"}), 500
        
    if not report_text.strip():
        return jsonify({"error": "No extractable text found in file."}), 400
        
    parsed_data = parse_report(report_text)
    features = extract_features(report_text)
    feature_frame = pd.DataFrame([features]).reindex(columns=feature_columns, fill_value=0.0)

    try:
        ml_probability = float(model.predict_proba(feature_frame)[0][1])
    except Exception as model_exc:
        return jsonify({"error": f"Model inference failed: {str(model_exc)}"}), 500
    ml_pred = 1 if ml_probability >= 0.5 else 0

    rules, reasons = rule_score(features)
    rule_pred = 1 if rules >= 3 else 0
    final_pred = 1 if (ml_pred == 1 or rule_pred == 1) else 0
    final_label = "SUSPICIOUS" if final_pred == 1 else "PROFESSIONAL"

    if final_pred == 0:
        reasons = ["No major authenticity red flags detected"]
    
    return jsonify({
        "status": "success",
        "result": final_label,
        "confidence": round(ml_probability, 4),
        "rule_score": rules,
        "reasons": reasons,
        "features": features,
        "extracted_data": parsed_data,
        "raw_text": report_text
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
