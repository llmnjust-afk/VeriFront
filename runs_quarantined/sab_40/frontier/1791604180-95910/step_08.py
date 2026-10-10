#!/usr/bin/env python3
import os
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
BASE = Path("benchmark/datasets/dili_MD")
OUTDIR = Path("pred_results")
OUTDIR.mkdir(exist_ok=True)

print("Starting fast RF training/prediction run", flush=True)
print("cwd:", os.getcwd(), flush=True)

train_df = pd.read_csv(BASE / "mol_descriptors_training.csv")
test_df = pd.read_csv(BASE / "test.csv")
meta = pd.read_csv(BASE / "standardized_compounds_excl_ambiguous_cluster.csv")
print("Loaded train/test/meta:", train_df.shape, test_df.shape, meta.shape, flush=True)

drop_cols = [c for c in train_df.columns if c.startswith("Unnamed")]
feature_cols = [c for c in train_df.columns if c not in drop_cols]
X_all = train_df[feature_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
X_test = test_df[feature_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
print("Feature cols:", len(feature_cols), "drop cols:", drop_cols, flush=True)
print("Label counts raw:", meta["vDILIConcern"].value_counts().to_dict(), flush=True)

split_defs = {
    "MCNC": {
        "DILI": {"vMost-DILI-Concern"},
        "NoDILI": {"vNo-DILI-Concern"},
    },
    "MCLCNC": {
        "DILI": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "NoDILI": {"vNo-DILI-Concern"},
    },
    "all": {
        "DILI": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "NoDILI": {"vNo-DILI-Concern", "sider_inactive"},
    },
}

# Compact but real hyperparameter search. Feature selection speeds RF and reduces descriptor noise.
candidates = [
    dict(n_estimators=250, max_features="sqrt", max_depth=None, min_samples_leaf=1, class_weight="balanced_subsample"),
    dict(n_estimators=250, max_features="sqrt", max_depth=20, min_samples_leaf=1, class_weight="balanced"),
    dict(n_estimators=300, max_features=0.25, max_depth=None, min_samples_leaf=2, class_weight="balanced_subsample"),
    dict(n_estimators=200, max_features="log2", max_depth=None, min_samples_leaf=1, class_weight="balanced"),
    dict(n_estimators=300, max_features=0.35, max_depth=16, min_samples_leaf=2, class_weight="balanced"),
    dict(n_estimators=200, max_features="sqrt", max_depth=10, min_samples_leaf=4, class_weight="balanced"),
]

summary = {}
for split_name, defs in split_defs.items():
    t0 = time.time()
    y_list, keep = [], []
    for v in meta["vDILIConcern"].tolist():
        if v in defs["DILI"]:
            y_list.append("DILI")
            keep.append(True)
        elif v in defs["NoDILI"]:
            y_list.append("NoDILI")
            keep.append(True)
        else:
            y_list.append(None)
            keep.append(False)
    keep = np.array(keep, dtype=bool)
    X = X_all.loc[keep].reset_index(drop=True)
    y = np.array(y_list, dtype=object)[keep]
    vc = pd.Series(y).value_counts().to_dict()
    print("\n==", split_name, "==", flush=True)
    print("Rows/features/classes:", X.shape[0], X.shape[1], vc, flush=True)

    # Single stratified validation split for fast hyperparameter search.
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_STATE)
    tr_idx, va_idx = next(splitter.split(X, y))
    X_tr, X_va = X.iloc[tr_idx], X.iloc[va_idx]
    y_tr, y_va = y[tr_idx], y[va_idx]

    # Choose top descriptors on training fold only. k capped to avoid slow high-dimensional RF.
    k = min(350, X.shape[1])
    best = None
    scores = []
    for i, params in enumerate(candidates, start=1):
        model = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("var", VarianceThreshold(threshold=0.0)),
            ("select", SelectKBest(score_func=f_classif, k=k)),
            ("rf", RandomForestClassifier(
                random_state=RANDOM_STATE + i,
                n_jobs=-1,
                bootstrap=True,
                **params
            )),
        ])
        st = time.time()
        model.fit(X_tr, y_tr)
        pred_va = model.predict(X_va)
        score = balanced_accuracy_score(y_va, pred_va)
        scores.append((score, params))
        print(f"candidate {i}/{len(candidates)} bal_acc={score:.4f} time={time.time()-st:.1f}s params={params}", flush=True)
        if best is None or score > best[0]:
            best = (score, params)

    best_score, best_params = best
    print("Best validation balanced accuracy:", best_score, flush=True)
    print("Best params:", best_params, flush=True)

    final_model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("var", VarianceThreshold(threshold=0.0)),
        ("select", SelectKBest(score_func=f_classif, k=k)),
        ("rf", RandomForestClassifier(
            random_state=RANDOM_STATE,
            n_jobs=-1,
            bootstrap=True,
            **best_params
        )),
    ])
    final_model.fit(X, y)

    # Training-set fitted prediction diagnostic, not used as unbiased metric.
    train_pred = final_model.predict(X)
    train_bal = balanced_accuracy_score(y, train_pred)
    print("Refit train balanced accuracy diagnostic:", train_bal, flush=True)
    print("Refit train confusion matrix labels [DILI, NoDILI]:", flush=True)
    print(confusion_matrix(y, train_pred, labels=["DILI", "NoDILI"]), flush=True)

    test_pred = final_model.predict(X_test)
    pred_counts = pd.Series(test_pred).value_counts().to_dict()
    print("Test prediction counts:", pred_counts, flush=True)

    out = test_df.copy()
    out["label"] = test_pred
    out_path = OUTDIR / f"MD_{split_name}_RF.csv"
    out.to_csv(out_path, index=False)
    pd.DataFrame({"label": test_pred}).to_csv(OUTDIR / f"MD_{split_name}_RF_labels_only.csv", index=False)
    print("Saved", out_path, "shape", out.shape, "elapsed split", time.time() - t0, flush=True)

    summary[split_name] = {
        "n_train": int(X.shape[0]),
        "class_counts": vc,
        "validation_balanced_accuracy": float(best_score),
        "train_balanced_accuracy_diagnostic": float(train_bal),
        "best_params": best_params,
        "all_candidate_scores": [{"balanced_accuracy": float(s), "params": p} for s, p in scores],
        "test_prediction_counts": pred_counts,
        "output": str(out_path),
    }

with open(OUTDIR / "MD_RF_training_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\nFinished all splits.", flush=True)
print("Required output pred_results/MD_MCNC_RF.csv exists:", (OUTDIR / "MD_MCNC_RF.csv").exists(), flush=True)
print(json.dumps(summary, indent=2), flush=True)