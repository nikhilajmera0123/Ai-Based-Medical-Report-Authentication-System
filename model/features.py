import re
from typing import Dict, List


DEFAULT_EXTRACTED = {
    "Doctor_Name": "Unknown",
    "Qualification": "Unknown",
    "Hospital_Name": "Unknown",
    "Age": -1,
    "Diagnosis": "Unknown",
    "Medicine_1": "Unknown",
    "Dose_1": "Unknown",
    "Medicine_2": "Unknown",
    "Dose_2": "Unknown",
}


def _first_match(patterns: List[str], text: str):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def parse_report(text: str) -> Dict[str, object]:
    data = DEFAULT_EXTRACTED.copy()
    if not text:
        return data

    doc = _first_match(
        [r"doctor(?:\s*name)?\s*[:\-]\s*(.+)", r"dr\.\s*([A-Za-z .]+)"],
        text,
    )
    if doc:
        data["Doctor_Name"] = doc

    qual = _first_match([r"qualification\s*[:\-]\s*(.+)"], text)
    if qual:
        data["Qualification"] = qual

    hosp = _first_match(
        [r"hospital(?:\s*name)?\s*[:\-]\s*(.+)", r"clinic\s*[:\-]\s*(.+)"],
        text,
    )
    if hosp:
        data["Hospital_Name"] = hosp

    age = _first_match([r"(?:patient\s*)?age\s*[:\-]?\s*(-?\d{1,3}|unknown)"], text)
    if age and age.lower() != "unknown":
        try:
            data["Age"] = float(age)
        except ValueError:
            data["Age"] = -1

    diag = _first_match([r"diagnosis\s*[:\-]\s*(.+)"], text)
    if diag:
        data["Diagnosis"] = diag

    med1 = _first_match([r"medicine\s*1\s*[:\-]\s*(.+)"], text)
    if med1:
        data["Medicine_1"] = med1

    dose1 = _first_match([r"dose\s*1\s*[:\-]\s*(.+)"], text)
    if dose1:
        data["Dose_1"] = dose1

    med2 = _first_match([r"medicine\s*2\s*[:\-]\s*(.+)"], text)
    if med2:
        data["Medicine_2"] = med2

    dose2 = _first_match([r"dose\s*2\s*[:\-]\s*(.+)"], text)
    if dose2:
        data["Dose_2"] = dose2

    return data


def _safe_age(text: str) -> float:
    match = re.search(r"(?:patient\s*)?age\s*[:\-]?\s*(-?\d{1,3})", text, re.IGNORECASE)
    if not match:
        return -1.0
    try:
        return float(match.group(1))
    except ValueError:
        return -1.0


def extract_features(text: str) -> Dict[str, float]:
    normalized_text = (text or "").lower()
    age_value = _safe_age(normalized_text)
    words = re.findall(r"\S+", normalized_text)
    alpha_words = re.findall(r"[a-z]+", normalized_text)

    dose_patterns = re.findall(r"\b\d+\s*-\s*\d+\s*-\s*\d+\b", normalized_text)
    mg_values = [float(v) for v in re.findall(r"(\d+(?:\.\d+)?)\s*mg\b", normalized_text)]

    unknown_markers = [
        "unknown",
        "n/a",
        "invalid",
        "pending",
        "every hour",
        "drink full bottle",
        "as much as you want",
    ]
    unknown_count = sum(normalized_text.count(marker) for marker in unknown_markers)

    medicine_mentions = len(re.findall(r"\b(medicine|tablet|syrup|mg|ml)\b", normalized_text))
    lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    key_value_lines = sum(1 for line in lines if ":" in line)

    features = {
        "age_value": age_value,
        "age_valid": 1.0 if 0 < age_value < 120 else 0.0,
        "has_doctor": 1.0 if ("doctor" in normalized_text or "dr." in normalized_text) else 0.0,
        "has_hospital": 1.0 if ("hospital" in normalized_text or "clinic" in normalized_text) else 0.0,
        "has_qualification": 1.0 if "qualification" in normalized_text else 0.0,
        "has_diagnosis": 1.0 if "diagnosis" in normalized_text else 0.0,
        "medicine_count": float(medicine_mentions),
        "dose_pattern_count": float(len(dose_patterns)),
        "dosage_extreme_flag": 1.0 if any(v > 2000 for v in mg_values) else 0.0,
        "text_length": float(len(normalized_text)),
        "word_count": float(len(words)),
        "alpha_word_ratio": float(len(alpha_words)) / (len(words) + 1.0),
        "unknown_tokens_ratio": float(unknown_count) / (len(words) + 1.0),
        "field_coverage_ratio": float(key_value_lines) / (len(lines) + 1.0),
        "non_ascii_ratio": float(sum(1 for ch in normalized_text if ord(ch) > 127))
        / (len(normalized_text) + 1.0),
    }
    return features


def build_training_text(record: Dict[str, object]) -> str:
    def _safe(value):
        if value is None:
            return "Unknown"
        return str(value)

    return "\n".join(
        [
            f"Doctor Name: {_safe(record.get('Doctor_Name'))}",
            f"Qualification: {_safe(record.get('Qualification'))}",
            f"Hospital Name: {_safe(record.get('Hospital_Name'))}",
            f"Patient Age: {_safe(record.get('Age'))}",
            f"Diagnosis: {_safe(record.get('Diagnosis'))}",
            f"Medicine 1: {_safe(record.get('Medicine_1'))}",
            f"Dose 1: {_safe(record.get('Dose_1'))}",
            f"Medicine 2: {_safe(record.get('Medicine_2'))}",
            f"Dose 2: {_safe(record.get('Dose_2'))}",
        ]
    )
