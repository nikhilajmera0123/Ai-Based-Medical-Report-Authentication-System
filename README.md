# 🏥 AI-Based Medical Report Authentication System

An intelligent system designed to detect **fraudulent medical reports and prescriptions** using Machine Learning, OCR, and rule-based validation.

This project analyzes uploaded medical documents (PDF/images), extracts text using OCR, and classifies them as **Professional (Real)** or **Suspicious (Fake)** with an explainable scoring system.

---

## 🚀 Features

- 📄 Upload medical reports (PDF/Image)
- 🔍 OCR-based text extraction using PyTesseract
- 🧠 Machine Learning model (Random Forest)
- 📊 TF-IDF based feature extraction
- ⚠️ Rule-based anomaly detection
- 📈 Classification: Professional vs Suspicious
- 🧾 Explainable output with confidence score
- 🌐 Flask-based web interface

---

## 🧠 Tech Stack

- **Language:** Python  
- **Framework:** Flask  
- **Machine Learning:** Scikit-learn (Random Forest)  
- **OCR:** PyTesseract  
- **NLP:** TF-IDF Vectorizer  
- **PDF Processing:** PyMuPDF / pdfplumber  

---

## ⚙️ How It Works

1. User uploads a medical report (PDF/Image)
2. OCR extracts text from the document
3. Text is preprocessed (cleaning, tokenization)
4. Features are generated using TF-IDF
5. ML model classifies the report
6. Rule-based checks validate anomalies
7. Final result is displayed with explanation

---

## 📊 Model Details

- Algorithm: Random Forest Classifier  
- Training Data: Synthetic + real-world inspired dataset  
- Features: TF-IDF vectors + rule-based indicators  
- Output:  
  - **Professional (Genuine)**  
  - **Suspicious (Fraudulent)**  

---

## 📁 Project Structure


├── app.py # Flask app
├── model/
│ ├── model.pkl # Trained ML model
│ └── vectorizer.pkl # TF-IDF vectorizer
├── utils/
│ ├── ocr.py # OCR processing
│ ├── preprocessing.py # Text cleaning
│ └── rules.py # Rule-based validation
├── templates/ # HTML frontend
├── static/ # CSS/JS files
└── uploads/ # Uploaded files


---

## ▶️ Installation & Setup

```bash
# Clone the repository
git clone https://github.com/your-username/medical-report-authentication.git

# Navigate to project
cd medical-report-authentication

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```
