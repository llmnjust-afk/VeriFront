#!/usr/bin/env python3
from pathlib import Path
import json
import warnings
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, f1_score, accuracy_score
from sklearn.model_selection import StratifiedShuffleSplit

warnings.filterwarnings("ignore")

t0 = time.time()
DATA_DIR = Path("benchmark/datasets/dili_MD")
if not (DATA_DIR / "mol_descriptors_training.csv").exists():
    DATA_DIR = Path("dili_MD")
if not (DATA_DIR / "mol_descriptors_training.csv").exists():
    raise FileNotFoundError("Could not locate dili_MD data")

OUT_DIR = Path("pred_results")
OUT_DIR.mkdir(exist_ok=True)

print("Using data:", DATA_DIR.resolve(), flush=True)
train_desc = pd.read_csv(DATA_DIR / "mol_descriptors_training.csv")
meta = pd.read_csv(DATA_DIR / "standardized_compounds_excl_ambiguous_cluster.csv")
test_desc = pd.read_csv(DATA_DIR / "test.csv")
print("Shapes train/meta/test:", train_desc.shape, meta.shape, test_desc.shape, flush=True)
print("Concern counts:", meta["vDILIConcern"].value_counts().to_dict(), flush=True)

def clean(df):
    df = df.copy()
    drop = [c for c in df.columns if c.startswith("Unnamed")]
    if drop:
        df = df.drop(columns=drop)
    # all descriptor columns should already be numeric; coerce defensively
    return df.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)

X_all_df = clean(train_desc)
X_test_df = clean(test_desc)
cols = [c for c in X_all_df.columns if c in X_test_df.columns]
X_all_df = X_all_df[cols]
X_test_df = X_test_df[cols]
print("Common descriptor columns:", len(cols), flush=True)

# One imputer fit on all descriptor-training rows; RF then receives dense numeric arrays.
imputer = SimpleImputer(strategy="median")
X_all_imp = imputer.fit_transform(X_all_df)
X_test_imp = imputer.transform(X_test_df)
print("Imputed arrays:", X_all_imp.shape, X_test_imp.shape, "elapsed", round(time.time() - t0, 1), flush=True)

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

# Compact hyperparameter search to stay within benchmark runtime.
param_grid = [
    dict(n_estimators=120, max_features="sqrt", max_depth=None, min_samples_leaf=1, class_weight="balanced_subsample"),
    dict(n_estimators=120, max_features="log2", max_depth=None, min_samples_leaf=1, class_weight="balanced_subsample"),
    dict(n_estimators=160, max_features=0.20, max_depth=None, min_samples_leaf=1, class_weight="balanced_subsample"),
    dict(n_estimators=160, max_features="sqrt", max_depth=12, min_samples_leaf=1, class_weight="balanced_subsample"),
    dict(n_estimators=160, max_features="sqrt", max_depth=None, min_samples_leaf=2, class_weight="balanced"),
    dict(n_estimators=200, max_features=0.35, max_depth=18, min_samples_leaf=2, class_weight="balanced_subsample"),
]
summary = {}

concerns = meta["vDILIConcern"].astype(str)

for split_name, spec in split_defs.items():
    print("\n===", split_name, "===", flush=True)
    mask = concerns.isin(spec["include"]).to_numpy()
    idx = np.flatnonzero(mask)
    sub_concerns = concerns.iloc[idx].reset_index(drop=True)
    y = np.where(sub_concerns.isin(spec["dili"]), 1, 0)
    X = X_all_imp[idx, :]

    print("Training n/features:", X.shape, flush=True)
    print("Binary counts:", pd.Series(np.where(y == 1, "DILI", "NoDILI")).value_counts().to_dict(), flush=True)

    # Stratified validation split for hyperparameter selection.
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=2026)
    tr_idx, va_idx = next(sss.split(X, y))
    X_tr, X_va = X[tr_idx], X[va_idx]
    y_tr, y_va = y[tr_idx], y[va_idx]

    best = None
    trials = []
    for k, params in enumerate(param_grid, 1):
        clf = RandomForestClassifier(
            random_state=2026 + k,
            n_jobs=-1,
            bootstrap=True,
            **params
        )
        clf.fit(X_tr, y_tr)
        pred_va = clf.predict(X_va)
        bal = balanced_accuracy_score(y_va, pred_va)
        f1m = f1_score(y_va, pred_va, average="macro")
        acc = accuracy_score(y_va, pred_va)
        rec = {"params": params, "balanced_accuracy": float(bal), "f1_macro": float(f1m), "accuracy": float(acc)}
        trials.append(rec)
        print("trial", k, "bal_acc", round(bal, 4), "f1_macro", round(f1m, 4), "params", params, flush=True)
        key = (bal, f1m, acc)
        if best is None or key > best[0]:
            best = (key, params)

    best_params = dict(best[1])
    # Refit on all split examples. Slightly increase tree count for stable final predictions.
    best_params["n_estimators"] = max(300, int(best_params["n_estimators"]))
    final_clf = RandomForestClassifier(
        random_state=4242,
        n_jobs=-1,
        bootstrap=True,
        **best_params
    )
    final_clf.fit(X, y)
    pred = final_clf.predict(X_test_imp)
    pred_labels = np.where(pred == 1, "DILI", "NoDILI")

    out = test_desc.copy()
    out["label"] = pred_labels
    out_path = OUT_DIR / f"MD_{split_name}_RF.csv"
    out.to_csv(out_path, index=False)

    pred_counts = pd.Series(pred_labels).value_counts().to_dict()
    print("Selected params:", best_params, flush=True)
    print("Prediction counts:", pred_counts, flush=True)
    print("Saved", out_path, "shape", out.shape, "size", out_path.stat().st_size, flush=True)

    summary[split_name] = {
        "n_train": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "label_counts": pd.Series(np.where(y == 1, "DILI", "NoDILI")).value_counts().to_dict(),
        "validation_trials": trials,
        "selected_params": best_params,
        "prediction_counts": pred_counts,
        "output": str(out_path),
    }

summary_path = OUT_DIR / "MD_RF_training_summary.json"
summary_path.write_text(json.dumps(summary, indent=2))
required = OUT_DIR / "MD_MCNC_RF.csv"
print("\nDONE elapsed_sec", round(time.time() - t0, 1), flush=True)
print("Summary saved:", summary_path, flush=True)
print("Required output exists:", required.exists(), "size:", required.stat().st_size if required.exists() else None, flush=True)
print("First output labels:", pd.read_csv(required)["label"].head(10).tolist(), flush=True)