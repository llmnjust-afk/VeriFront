#!/usr/bin/env python3
import os
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, make_scorer, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

RANDOM_STATE = 42
BASE = Path("benchmark/datasets/dili_MD")
OUTDIR = Path("pred_results")
OUTDIR.mkdir(exist_ok=True)

train_X_raw = pd.read_csv(BASE / "mol_descriptors_training.csv")
test_X_raw = pd.read_csv(BASE / "test.csv")
meta = pd.read_csv(BASE / "standardized_compounds_excl_ambiguous_cluster.csv")

print("Loaded:")
print("  train descriptors:", train_X_raw.shape)
print("  test descriptors :", test_X_raw.shape)
print("  metadata         :", meta.shape)
print("  label counts:")
print(meta["vDILIConcern"].value_counts().to_string())

# Drop CSV index column; keep feature columns consistent.
drop_cols = [c for c in train_X_raw.columns if c.startswith("Unnamed")]
feature_cols = [c for c in train_X_raw.columns if c not in drop_cols]
X_all = train_X_raw[feature_cols].copy()
X_test = test_X_raw[feature_cols].copy()

# Ensure all features numeric and finite.
X_all = X_all.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
X_test = X_test.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)

print("Feature matrix after dropping index columns:", X_all.shape)
print("Missing values train/test:", int(X_all.isna().sum().sum()), int(X_test.isna().sum().sum()))

split_defs = {
    # Most-DILI-Concern vs No-DILI-Concern
    "MCNC": {
        "DILI": {"vMost-DILI-Concern"},
        "NoDILI": {"vNo-DILI-Concern"},
    },
    # Most/Less-DILI-Concern vs No-DILI-Concern
    "MCLCNC": {
        "DILI": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "NoDILI": {"vNo-DILI-Concern"},
    },
    # All examples: Most/Less as DILI, No/sider_inactive as NoDILI
    "all": {
        "DILI": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "NoDILI": {"vNo-DILI-Concern", "sider_inactive"},
    },
}

param_distributions = {
    "rf__n_estimators": [300, 500, 800],
    "rf__max_features": ["sqrt", "log2", 0.2, 0.35, 0.5],
    "rf__max_depth": [None, 8, 12, 20, 35],
    "rf__min_samples_split": [2, 5, 10],
    "rf__min_samples_leaf": [1, 2, 4],
    "rf__class_weight": ["balanced", "balanced_subsample", None],
}

summary = {}

for split_name, defs in split_defs.items():
    labels = []
    mask = []
    for lab in meta["vDILIConcern"]:
        if lab in defs["DILI"]:
            labels.append("DILI")
            mask.append(True)
        elif lab in defs["NoDILI"]:
            labels.append("NoDILI")
            mask.append(True)
        else:
            labels.append(None)
            mask.append(False)

    mask = np.array(mask, dtype=bool)
    y = np.array(labels, dtype=object)[mask]
    X = X_all.loc[mask].reset_index(drop=True)

    print("\n" + "=" * 80)
    print("Split:", split_name)
    print("Training rows:", X.shape[0], "features:", X.shape[1])
    print("Class counts:", pd.Series(y).value_counts().to_dict())

    min_class = pd.Series(y).value_counts().min()
    n_splits = int(min(5, min_class))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("rf", RandomForestClassifier(
            random_state=RANDOM_STATE,
            n_jobs=-1,
            bootstrap=True,
        )),
    ])

    search = RandomizedSearchCV(
        estimator=pipe,
        param_distributions=param_distributions,
        n_iter=18,
        scoring=make_scorer(balanced_accuracy_score),
        n_jobs=-1,
        cv=cv,
        verbose=0,
        random_state=RANDOM_STATE,
        refit=True,
        return_train_score=True,
    )
    search.fit(X, y)

    print("Best CV balanced accuracy:", float(search.best_score_))
    print("Best params:", search.best_params_)

    # Estimate out-of-fold performance for selected hyperparameters.
    best_model = search.best_estimator_
    oof = cross_val_predict(best_model, X, y, cv=cv, n_jobs=-1)
    bal_acc = balanced_accuracy_score(y, oof)
    print("OOF balanced accuracy (best params):", float(bal_acc))
    print("OOF confusion matrix labels ['DILI','NoDILI']:")
    print(confusion_matrix(y, oof, labels=["DILI", "NoDILI"]))
    print("OOF report:")
    print(classification_report(y, oof, digits=4))

    # Refit on all selected training data and predict benchmark test descriptors.
    best_model.fit(X, y)
    pred = best_model.predict(X_test)
    pred_counts = pd.Series(pred).value_counts().to_dict()
    print("Test prediction counts:", pred_counts)

    out = test_X_raw.copy()
    out["label"] = pred
    out_path = OUTDIR / f"MD_{split_name}_RF.csv"
    out.to_csv(out_path, index=False)
    print("Saved:", out_path, "shape:", out.shape)

    # Also save compact labels-only sidecar for easy inspection (not the required path).
    compact_path = OUTDIR / f"MD_{split_name}_RF_labels_only.csv"
    pd.DataFrame({"label": pred}).to_csv(compact_path, index=False)

    summary[split_name] = {
        "n_train": int(X.shape[0]),
        "class_counts": pd.Series(y).value_counts().to_dict(),
        "best_cv_balanced_accuracy": float(search.best_score_),
        "oof_balanced_accuracy": float(bal_acc),
        "best_params": search.best_params_,
        "test_prediction_counts": pred_counts,
        "output": str(out_path),
    }

summary_path = OUTDIR / "MD_RF_training_summary.json"
with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)
print("\nSummary saved:", summary_path)
print(json.dumps(summary, indent=2))
print("\nRequired output exists:", (OUTDIR / "MD_MCNC_RF.csv").exists())