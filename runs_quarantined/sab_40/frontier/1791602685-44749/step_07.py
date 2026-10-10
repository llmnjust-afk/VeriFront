#!/usr/bin/env python3
"""
Train Random Forest DILI classifiers on molecular descriptor features and save
predictions for the benchmark test descriptors.

Outputs:
  pred_results/MD_MCNC_RF.csv
  pred_results/MD_MCLCNC_RF.csv
  pred_results/MD_all_RF.csv
"""
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, f1_score, make_scorer
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore", category=UserWarning)

# Locate data
DATA_DIR_CANDIDATES = [Path("dili_MD"), Path("benchmark/datasets/dili_MD")]
DATA_DIR = None
for p in DATA_DIR_CANDIDATES:
    if (p / "mol_descriptors_training.csv").exists():
        DATA_DIR = p
        break
if DATA_DIR is None:
    raise FileNotFoundError("Could not find dili_MD dataset folder.")

OUT_DIR = Path("pred_results")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("Using data directory:", DATA_DIR.resolve())

# Load aligned training descriptors/metadata and benchmark test descriptors
X_train_raw = pd.read_csv(DATA_DIR / "mol_descriptors_training.csv")
meta = pd.read_csv(DATA_DIR / "standardized_compounds_excl_ambiguous_cluster.csv")
X_test_raw = pd.read_csv(DATA_DIR / "test.csv")

print("Loaded shapes:")
print("  descriptors training:", X_train_raw.shape)
print("  metadata:", meta.shape)
print("  test descriptors:", X_test_raw.shape)
print("Metadata label counts:")
print(meta["vDILIConcern"].value_counts().to_string())

if len(X_train_raw) != len(meta):
    raise ValueError("Training descriptors and metadata row counts differ; expected aligned rows.")

# Drop CSV index columns and keep common numeric descriptor columns in identical order.
def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    drop_cols = [c for c in df.columns if c.startswith("Unnamed")]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    # Coerce any non-numeric accidental values to NaN for imputation.
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    return df

X_all = clean_features(X_train_raw)
X_test = clean_features(X_test_raw)

common_cols = [c for c in X_all.columns if c in X_test.columns]
missing_test = [c for c in X_all.columns if c not in X_test.columns]
extra_test = [c for c in X_test.columns if c not in X_all.columns]
print(f"Feature columns: train={X_all.shape[1]}, test={X_test.shape[1]}, common={len(common_cols)}")
print("Missing from test:", missing_test[:10], "count", len(missing_test))
print("Extra in test:", extra_test[:10], "count", len(extra_test))

X_all = X_all[common_cols]
X_test = X_test[common_cols]

# Split definitions inferred from benchmark names:
# MCNC   : vMost-DILI-Concern vs vNo-DILI-Concern
# MCLCNC : vMost/vLess-DILI-Concern vs vNo-DILI-Concern
# all    : all rows, vMost/vLess-DILI-Concern as DILI and vNo/sider_inactive as NoDILI
split_defs = {
    "MCNC": {
        "include": {"vMost-DILI-Concern", "vNo-DILI-Concern"},
        "dili": {"vMost-DILI-Concern"},
        "nodili": {"vNo-DILI-Concern"},
    },
    "MCLCNC": {
        "include": {"vMost-DILI-Concern", "vLess-DILI-Concern", "vNo-DILI-Concern"},
        "dili": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "nodili": {"vNo-DILI-Concern"},
    },
    "all": {
        "include": {"vMost-DILI-Concern", "vLess-DILI-Concern", "vNo-DILI-Concern", "sider_inactive"},
        "dili": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "nodili": {"vNo-DILI-Concern", "sider_inactive"},
    },
}

# Moderate randomized hyperparameter search; random forest is robust to unscaled descriptor magnitudes.
param_distributions = {
    "rf__n_estimators": [300, 500, 800],
    "rf__max_features": ["sqrt", "log2", 0.2, 0.35, 0.5],
    "rf__max_depth": [None, 8, 12, 18, 25],
    "rf__min_samples_split": [2, 4, 8, 12],
    "rf__min_samples_leaf": [1, 2, 4],
    "rf__class_weight": ["balanced", "balanced_subsample", None],
    "rf__bootstrap": [True],
}

summary = {}

for split_name, spec in split_defs.items():
    concerns = meta["vDILIConcern"].astype(str)
    mask = concerns.isin(spec["include"]).to_numpy()
    X = X_all.loc[mask].reset_index(drop=True)
    concern_subset = concerns.loc[mask].reset_index(drop=True)

    y_labels = np.where(concern_subset.isin(spec["dili"]), "DILI", "NoDILI")
    y = np.where(y_labels == "DILI", 1, 0)

    print("\n=== Split", split_name, "===")
    print("Training rows:", X.shape[0], "features:", X.shape[1])
    print("Original concern counts:", concern_subset.value_counts().to_dict())
    print("Binary label counts:", pd.Series(y_labels).value_counts().to_dict())

    min_class = int(pd.Series(y).value_counts().min())
    n_splits = max(3, min(5, min_class))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=2026)

    pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("rf", RandomForestClassifier(random_state=2026, n_jobs=-1)),
        ]
    )

    search = RandomizedSearchCV(
        estimator=pipe,
        param_distributions=param_distributions,
        n_iter=24,
        scoring={
            "balanced_accuracy": make_scorer(balanced_accuracy_score),
            "f1_macro": make_scorer(f1_score, average="macro"),
        },
        refit="balanced_accuracy",
        cv=cv,
        random_state=2026,
        n_jobs=-1,
        verbose=0,
        return_train_score=False,
    )
    search.fit(X, y)

    print("Best CV balanced_accuracy:", round(float(search.best_score_), 4))
    print("Best params:", search.best_params_)

    best_model = search.best_estimator_
    # Additional f1 estimate for reporting with the selected hyperparameters.
    f1_scores = cross_val_score(best_model, X, y, cv=cv, scoring=make_scorer(f1_score, average="macro"), n_jobs=-1)
    print("Selected model CV f1_macro mean/std:", round(float(f1_scores.mean()), 4), round(float(f1_scores.std()), 4))

    # Refit on all rows in this split and predict benchmark test descriptors.
    best_model.fit(X, y)
    pred_num = best_model.predict(X_test)
    pred_labels = np.where(pred_num == 1, "DILI", "NoDILI")

    out = X_test_raw.copy()
    out["label"] = pred_labels
    out_path = OUT_DIR / f"MD_{split_name}_RF.csv"
    out.to_csv(out_path, index=False)

    print("Saved:", out_path, "shape:", out.shape)
    print("Prediction counts:", pd.Series(pred_labels).value_counts().to_dict())

    summary[split_name] = {
        "n_train": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "label_counts": pd.Series(y_labels).value_counts().to_dict(),
        "best_cv_balanced_accuracy": float(search.best_score_),
        "cv_f1_macro_mean": float(f1_scores.mean()),
        "cv_f1_macro_std": float(f1_scores.std()),
        "best_params": search.best_params_,
        "prediction_counts": pd.Series(pred_labels).value_counts().to_dict(),
        "output": str(out_path),
    }

summary_path = OUT_DIR / "MD_RF_training_summary.json"
summary_path.write_text(json.dumps(summary, indent=2))
print("\nWrote summary:", summary_path)
print("Required output exists:", (OUT_DIR / "MD_MCNC_RF.csv").exists(), "size:", (OUT_DIR / "MD_MCNC_RF.csv").stat().st_size)
print("All outputs in pred_results:", sorted(p.name for p in OUT_DIR.glob("MD_*_RF.csv")))