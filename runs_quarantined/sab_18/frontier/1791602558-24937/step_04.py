#!/usr/bin/env python3
import os
import warnings
import numpy as np
import pandas as pd

from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import balanced_accuracy_score, accuracy_score, roc_auc_score

warnings.filterwarnings("ignore", category=UserWarning)

TRAIN_PATH = "benchmark/datasets/dili/train.csv"
TEST_PATH = "benchmark/datasets/dili/test.csv"
OUT_DIR = "pred_results"
os.makedirs(OUT_DIR, exist_ok=True)

RANDOM_STATE = 42
N_BITS = 2048
RADIUS = 2

def smiles_to_morgan_array(smiles, n_bits=N_BITS, radius=RADIUS):
    mol = Chem.MolFromSmiles(str(smiles))
    arr = np.zeros((n_bits,), dtype=np.uint8)
    if mol is None:
        return arr
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def featurize(smiles_list):
    X = np.vstack([smiles_to_morgan_array(s) for s in smiles_list])
    return X

def make_dataset(train_df, config):
    vc = train_df["vDILIConcern"]
    if config == "MCNC":
        # Most-DILI concern versus No-DILI concern
        mask = vc.isin(["vMost-DILI-Concern", "vNo-DILI-Concern"])
        sub = train_df.loc[mask].copy()
        y = (sub["vDILIConcern"] == "vMost-DILI-Concern").astype(int).to_numpy()
    elif config == "MCLCNC":
        # Most/Less-DILI concern versus No-DILI concern
        mask = vc.isin(["vMost-DILI-Concern", "vLess-DILI-Concern", "vNo-DILI-Concern"])
        sub = train_df.loc[mask].copy()
        y = sub["vDILIConcern"].isin(["vMost-DILI-Concern", "vLess-DILI-Concern"]).astype(int).to_numpy()
    elif config == "all":
        # Most/Less-DILI concern versus No-DILI concern/sider inactive
        mask = vc.isin(["vMost-DILI-Concern", "vLess-DILI-Concern", "vNo-DILI-Concern", "sider_inactive"])
        sub = train_df.loc[mask].copy()
        y = sub["vDILIConcern"].isin(["vMost-DILI-Concern", "vLess-DILI-Concern"]).astype(int).to_numpy()
    else:
        raise ValueError(config)
    return sub, y

print("Loading data...")
train_df = pd.read_csv(TRAIN_PATH)
test_df = pd.read_csv(TEST_PATH)
print("train shape:", train_df.shape)
print("test shape:", test_df.shape)
print("train vDILIConcern counts:")
print(train_df["vDILIConcern"].value_counts().to_string())

print("\nFeaturizing test set once...")
X_test = featurize(test_df["standardised_smiles"].tolist())
print("X_test:", X_test.shape)

param_grid = {
    "n_estimators": [200, 500],
    "max_depth": [None, 10, 20],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [1, 2],
}

summary_rows = []
for config in ["MCNC", "MCLCNC", "all"]:
    print("\n" + "=" * 80)
    print("Configuration:", config)
    sub, y = make_dataset(train_df, config)
    print("Training examples:", len(sub))
    print("Class counts (0=NoDILI, 1=DILI):", dict(zip(*np.unique(y, return_counts=True))))
    print("Included concern counts:")
    print(sub["vDILIConcern"].value_counts().to_string())

    print("Featurizing train subset...")
    X = featurize(sub["standardised_smiles"].tolist())
    print("X:", X.shape)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    rf = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    grid = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        scoring="balanced_accuracy",
        cv=cv,
        n_jobs=-1,
        refit=True,
        verbose=1,
        return_train_score=True,
    )
    grid.fit(X, y)

    print("Best params:", grid.best_params_)
    print("Best mean CV balanced_accuracy:", grid.best_score_)

    best_model = grid.best_estimator_

    # Report out-of-fold-like fold scores using the selected hyperparameters for transparency.
    fold_bal_acc = []
    fold_acc = []
    fold_auc = []
    for fold, (tr_idx, va_idx) in enumerate(cv.split(X, y), start=1):
        model = RandomForestClassifier(
            random_state=RANDOM_STATE + fold,
            n_jobs=-1,
            class_weight="balanced_subsample",
            **grid.best_params_,
        )
        model.fit(X[tr_idx], y[tr_idx])
        pred = model.predict(X[va_idx])
        proba = model.predict_proba(X[va_idx])[:, 1]
        ba = balanced_accuracy_score(y[va_idx], pred)
        ac = accuracy_score(y[va_idx], pred)
        try:
            auc = roc_auc_score(y[va_idx], proba)
        except ValueError:
            auc = np.nan
        fold_bal_acc.append(ba)
        fold_acc.append(ac)
        fold_auc.append(auc)
        print(f"Fold {fold}: balanced_accuracy={ba:.4f}, accuracy={ac:.4f}, roc_auc={auc:.4f}")

    # GridSearchCV refit=True already trained best model on full config training set.
    test_pred = best_model.predict(X_test)
    labels = np.where(test_pred == 1, "DILI", "NoDILI")
    out_df = pd.DataFrame({
        "standardised_smiles": test_df["standardised_smiles"],
        "label": labels,
    })
    out_path = os.path.join(OUT_DIR, f"{config}_RF.csv")
    out_df.to_csv(out_path, index=False)
    print("Saved:", out_path)
    print("Prediction label counts:")
    print(out_df["label"].value_counts().to_string())

    summary_rows.append({
        "config": config,
        "n_train": len(sub),
        "n_pos": int(y.sum()),
        "n_neg": int((1 - y).sum()),
        "best_cv_balanced_accuracy": float(grid.best_score_),
        "selected_fold_balanced_accuracy_mean": float(np.mean(fold_bal_acc)),
        "selected_fold_accuracy_mean": float(np.mean(fold_acc)),
        "selected_fold_roc_auc_mean": float(np.nanmean(fold_auc)),
        "best_params": grid.best_params_,
        "out_path": out_path,
    })

summary = pd.DataFrame(summary_rows)
summary_path = os.path.join(OUT_DIR, "RF_training_summary.csv")
summary.to_csv(summary_path, index=False)
print("\n" + "=" * 80)
print("Summary:")
print(summary.to_string(index=False))
print("Saved summary:", summary_path)
print("Output files present:")
for fn in sorted(os.listdir(OUT_DIR)):
    if fn.endswith("_RF.csv") or fn == "RF_training_summary.csv":
        p = os.path.join(OUT_DIR, fn)
        print(p, os.path.getsize(p), "bytes")