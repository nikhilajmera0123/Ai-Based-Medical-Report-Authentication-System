import os
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from features import build_training_text, extract_features

def load_and_train():
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, "..", "data", "Large_Project_Data.csv")

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path, sep="\t")
    df = df.dropna(subset=["Record_Status"]).copy()

    feature_rows = []
    for _, row in df.iterrows():
        row_text = build_training_text(row.to_dict())
        feature_rows.append(extract_features(row_text))

    X = pd.DataFrame(feature_rows)
    y = (df["Record_Status"].str.upper() == "SUSPICIOUS").astype(int)

    print("Training logistic model with engineered features...")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Logistic Regression Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=["PROFESSIONAL", "SUSPICIOUS"]))

    model_path = os.path.join(current_dir, "hybrid_model.pkl")
    metadata_path = os.path.join(current_dir, "model_metadata.pkl")

    joblib.dump(clf, model_path)
    joblib.dump({"feature_columns": list(X.columns)}, metadata_path)

    print("Exported model to", model_path)
    print("Exported metadata to", metadata_path)

if __name__ == "__main__":
    load_and_train()
