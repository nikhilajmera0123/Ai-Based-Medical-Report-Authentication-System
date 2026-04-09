import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import train_test_split

from features import build_training_text, extract_features

def save_plot(name):
    current_dir = os.path.dirname(__file__)
    plots_dir = os.path.join(current_dir, "..", "assets", "plots")
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    path = os.path.join(plots_dir, name)
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    return path

def load_and_train():
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, "..", "data", "Large_Project_Data.csv")

    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path, sep="\t")
    df = df.dropna(subset=["Record_Status"]).copy()

    print("Extracting features from text...")
    feature_rows = []
    for _, row in df.iterrows():
        row_text = build_training_text(row.to_dict())
        feature_rows.append(extract_features(row_text))

    X = pd.DataFrame(feature_rows)
    y = (df["Record_Status"].str.upper() == "SUSPICIOUS").astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    }

    results = []
    trained_models = {}

    print("\nTraining and evaluating models...")
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        rec_suspicious = recall_score(y_test, preds) # Recall for class 1 (SUSPICIOUS)
        
        results.append({
            "Model": name,
            "Accuracy": acc,
            "F1 Score": f1,
            "Recall (SUSPICIOUS)": rec_suspicious
        })
        trained_models[name] = model
        
        print(f"{name} -> Accuracy: {acc:.4f}, F1: {f1:.4f}, Recall (Suspicious): {rec_suspicious:.4f}")

    results_df = pd.DataFrame(results)

    # 1. Model Comparison Chart
    plt.figure(figsize=(10, 6))
    df_melted = results_df.melt(id_vars="Model", var_name="Metric", value_name="Score")
    sns.barplot(data=df_melted, x="Metric", y="Score", hue="Model")
    plt.title("Model Performance Comparison (Focus on Fraud Detection)")
    plt.ylim(0, 1.1)
    save_plot("model_comparison.png")

    # Select Best Model based on Recall (SUSPICIOUS)
    best_model_name = results_df.sort_values(by="Recall (SUSPICIOUS)", ascending=False).iloc[0]["Model"]
    best_model = trained_models[best_model_name]
    best_recall = results_df[results_df["Model"] == best_model_name]["Recall (SUSPICIOUS)"].values[0]

    print(f"\nBest Model Selected: {best_model_name}")
    print(f"Reason: Highest Recall for SUSPICIOUS cases ({best_recall:.4f})")

    # 2. Confusion Matrix for Best Model
    plt.figure(figsize=(8, 6))
    best_preds = best_model.predict(X_test)
    cm = confusion_matrix(y_test, best_preds)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=["PROFESSIONAL", "SUSPICIOUS"],
                yticklabels=["PROFESSIONAL", "SUSPICIOUS"])
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"Confusion Matrix: {best_model_name}")
    save_plot("confusion_matrix.png")

    # 3. Feature Importance (Best Model or Random Forest)
    plt.figure(figsize=(10, 8))
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        feat_importances = pd.Series(importances, index=X.columns).sort_values(ascending=True)
        feat_importances.plot(kind='barh', color='teal')
        plt.title(f"Feature Importance: {best_model_name}")
    elif hasattr(best_model, 'coef_'):
        importances = abs(best_model.coef_[0])
        feat_importances = pd.Series(importances, index=X.columns).sort_values(ascending=True)
        feat_importances.plot(kind='barh', color='salmon')
        plt.title(f"Feature Importance (Coefficients): {best_model_name}")
    
    plt.xlabel("Relative Importance")
    save_plot("feature_importance.png")

    # Export
    model_path = os.path.join(current_dir, "best_model.pkl")
    metadata_path = os.path.join(current_dir, "model_metadata.pkl")

    joblib.dump(best_model, model_path)
    joblib.dump({"feature_columns": list(X.columns), "model_name": best_model_name}, metadata_path)

    print(f"\nExported {best_model_name} to {model_path}")
    print("Exported metadata to", metadata_path)
    print("\nAll visualizations saved to assets/plots/")

if __name__ == "__main__":
    load_and_train()
