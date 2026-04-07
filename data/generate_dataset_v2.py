import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


@dataclass
class Record:
    Doctor_Name: str
    Qualification: str
    Hospital_Name: str
    Age: str
    Diagnosis: str
    Medicine_1: str
    Dose_1: str
    Medicine_2: str
    Dose_2: str
    Record_Status: str
    Sample_Type: str


DOCTORS = [
    "Dr. Anil Deshmukh",
    "Dr. Kavita Iyer",
    "Dr. Meera Reddy",
    "Dr. Sameer Joshi",
    "Dr. Arjun Mehra",
    "Dr. Nisha Verma",
    "Dr. Rohit Kulkarni",
]

QUALIFICATIONS = ["MBBS", "MBBS, MD", "MBBS, DNB", "BAMS", "BHMS"]
HOSPITALS = [
    "City Care Hospital",
    "Arogya Clinic",
    "Apollo Health",
    "Fortis Memorial",
    "Max Super Specialty",
    "Sunrise Multispeciality",
]

DIAGNOSIS_TO_MEDS: Dict[str, List[Tuple[str, str]]] = {
    "Viral Fever": [("Dolo 650mg", "1-0-1"), ("Ascoril LS", "1-0-0"), ("Limcee 500mg", "1-0-1")],
    "Hypertension": [("Telma 40mg", "1-0-0"), ("Amlokind 5mg", "1-0-0"), ("Aten 50mg", "1-0-1")],
    "Type 2 Diabetes": [("Glycomet GP 500", "1-0-1"), ("Voglibose 0.2mg", "1-0-1"), ("Teneligliptin 20mg", "1-0-0")],
    "Gastroenteritis": [("Norflox TZ", "1-0-1"), ("Pan-40", "1-0-1"), ("Econorm", "1-0-0")],
    "Acute Bronchitis": [("Augmentin 625mg", "1-0-1"), ("Ascoril LS", "1-0-1"), ("Azithral 500", "1-0-0")],
    "Migraine": [("Sibelium 10", "0-0-1"), ("Naprosyn 250", "1-0-1"), ("Domstal", "1-1-1")],
}

def rng_choice(items):
    return random.choice(items)


def sample_real_record() -> Record:
    diagnosis = rng_choice(list(DIAGNOSIS_TO_MEDS.keys()))
    med_pool = DIAGNOSIS_TO_MEDS[diagnosis]
    m1 = rng_choice(med_pool)
    m2 = rng_choice(med_pool)
    return Record(
        Doctor_Name=rng_choice(DOCTORS),
        Qualification=rng_choice(QUALIFICATIONS[:3]),
        Hospital_Name=rng_choice(HOSPITALS),
        Age=str(random.randint(18, 85)),
        Diagnosis=diagnosis,
        Medicine_1=m1[0],
        Dose_1=m1[1],
        Medicine_2=m2[0],
        Dose_2=m2[1],
        Record_Status="PROFESSIONAL",
        Sample_Type="REAL_CLEAN",
    )


def sample_obvious_fraud() -> Record:
    weird_dose = rng_choice(["50000 mg", "Every hour", "Drink full bottle", "As much as you want"])
    return Record(
        Doctor_Name=rng_choice(["Dr. X", "Unknown", "Local Compounder", "Medical Expert"]),
        Qualification=rng_choice(["None", "Invalid", "Health Guru", ""]),
        Hospital_Name=rng_choice(["N/A", "Invalid", "Pending", "Local Medical / Home Visit"]),
        Age=rng_choice(["-10", "160", "Unknown", "140"]),
        Diagnosis=rng_choice(["Checking", "Body pain", "Stomach issue", "Feeling sick"]),
        Medicine_1=rng_choice(["Random Tablet", "Unknown Syrup", "Experimental Mix"]),
        Dose_1=weird_dose,
        Medicine_2=rng_choice(["Random Tablet", "Unknown Syrup", "Mystery Capsule"]),
        Dose_2=rng_choice(["50000 mg", "Every hour", "Drink full bottle", "0.0001 ml"]),
        Record_Status="SUSPICIOUS",
        Sample_Type="OBVIOUS_FRAUD",
    )


def make_subtle_fraud(real: Record) -> Record:
    mutated = Record(**real.__dict__)
    mutation = rng_choice(
        [
            "dose_format",
            "age_edge",
            "qualification_mismatch",
            "field_missing",
            "cross_diagnosis_mismatch",
        ]
    )

    if mutation == "dose_format":
        mutated.Dose_1 = rng_choice(["10-10-10-10", "1/0/1", "morning-night", "11-0-11"])
    elif mutation == "age_edge":
        mutated.Age = rng_choice(["0", "121", "125", "Unknown"])
    elif mutation == "qualification_mismatch":
        mutated.Qualification = rng_choice(["None", "Intern", "Diploma", ""])
    elif mutation == "field_missing":
        missing_field = rng_choice(["Doctor_Name", "Hospital_Name", "Diagnosis"])
        setattr(mutated, missing_field, rng_choice(["Unknown", "N/A", ""]))
    elif mutation == "cross_diagnosis_mismatch":
        other_diag = rng_choice([d for d in DIAGNOSIS_TO_MEDS.keys() if d != real.Diagnosis])
        mismed = rng_choice(DIAGNOSIS_TO_MEDS[other_diag])
        mutated.Medicine_2 = mismed[0]
        mutated.Dose_2 = mismed[1]

    mutated.Record_Status = "SUSPICIOUS"
    mutated.Sample_Type = "SUBTLE_FRAUD"
    return mutated


def ocr_noise(text: str) -> str:
    replacements = {
        "0": "O",
        "O": "0",
        "1": "l",
        "l": "1",
        "m": "rn",
        "rn": "m",
        "S": "5",
        "5": "S",
        "a": "@",
    }
    out = []
    for ch in text:
        if random.random() < 0.06 and ch in replacements:
            out.append(replacements[ch])
        elif random.random() < 0.02 and ch == " ":
            continue
        else:
            out.append(ch)
    return "".join(out)


def make_ocr_variant(base: Record) -> Record:
    noisy = Record(**base.__dict__)
    noisy.Doctor_Name = ocr_noise(noisy.Doctor_Name)
    noisy.Hospital_Name = ocr_noise(noisy.Hospital_Name)
    noisy.Diagnosis = ocr_noise(noisy.Diagnosis)
    noisy.Medicine_1 = ocr_noise(noisy.Medicine_1)
    noisy.Dose_1 = ocr_noise(noisy.Dose_1)
    noisy.Medicine_2 = ocr_noise(noisy.Medicine_2)
    noisy.Dose_2 = ocr_noise(noisy.Dose_2)
    noisy.Sample_Type = "OCR_NOISE"
    return noisy


def generate_dataset(total_rows: int = 12000, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    n_real = int(total_rows * 0.40)
    n_subtle = int(total_rows * 0.30)
    n_obvious = int(total_rows * 0.20)
    n_ocr = total_rows - (n_real + n_subtle + n_obvious)

    rows: List[Record] = []

    real_rows = [sample_real_record() for _ in range(n_real)]
    rows.extend(real_rows)

    for _ in range(n_subtle):
        rows.append(make_subtle_fraud(sample_real_record()))

    for _ in range(n_obvious):
        rows.append(sample_obvious_fraud())

    # OCR variants: mostly real + some subtle fraud
    for _ in range(n_ocr):
        if random.random() < 0.7:
            base = sample_real_record()
            base.Record_Status = "PROFESSIONAL"
        else:
            base = make_subtle_fraud(sample_real_record())
            base.Record_Status = "SUSPICIOUS"
        rows.append(make_ocr_variant(base))

    random.shuffle(rows)
    df = pd.DataFrame([r.__dict__ for r in rows])
    return df


def main():
    out_path = Path(__file__).with_name("Large_Project_Data.csv")
    df = generate_dataset(total_rows=12000, seed=42)
    df.to_csv(out_path, sep="\t", index=False)

    print(f"Generated {len(df)} rows at: {out_path}")
    print("\nRecord_Status distribution:")
    print(df["Record_Status"].value_counts())
    print("\nSample_Type distribution:")
    print(df["Sample_Type"].value_counts())


if __name__ == "__main__":
    main()
