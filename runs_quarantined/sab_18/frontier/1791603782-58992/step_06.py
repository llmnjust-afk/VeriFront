#!/usr/bin/env python3
import os
import time
import warnings
import numpy as np
import pandas as pd

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold

warnings.filterwarnings("ignore")
RDLogger.DisableLog("rdApp.*")

RANDOM_STATE = 42
TRAIN_PATH = "benchmark/datasets/dili/train.csv"
TEST_PATH = "benchmark/datasets/dili/test.csv"
OUT_DIR = "pred_results"
os.makedirs(OUT_DIR, exist_ok=True)

def log(*args):
    print(*args, flush=True)

def smiles_to_morgan(smiles, n_bits=1024, radius=2):
    arr = np.zeros((n_bits,), dtype=np.uint8)
    if not isinstance(smiles, str) or not smiles.strip():
        return arr
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return arr
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def featurize(smiles_series):
    return np.vstack([smiles_to_morgan(s) for s in smiles_series])

def task_dataframe(train, conf):
    # Problem statement split is 1-based:
    # MC 1-173, LC 174-433, NC 434-660, sider 661-923
    mc = train.iloc[0:173].copy()
    lc = train.iloc[173:433].copy()
    nc = train.iloc[433:660].copy()
    sider = train.iloc[660:923].copy()

    if conf == "MCNC":
        df = pd.concat([mc, nc], ignore_index=True)
        y = np.r_[np.ones(len(mc), dtype=int), np.zeros(len(nc), dtype=int)]
    elif conf == "MCLCNC":
        pos = pd.concat([mc, lc], ignore_index=True)
        df = pd.concat([pos, nc], ignore_index=True)
        y = np.r_[np.ones(len(pos), dtype=int), np.zeros(len(nc), dtype=int)]
    elif conf == "all":
        pos = pd.concat([mc, lc], ignore_index=True)
        neg = pd.concat([nc, sider], ignore_index=True)
        df = pd.concat([pos, neg], ignore_index=True)
        y = np.r_[np.ones(len(pos), dtype=int), np.zeros(len(neg), dtype=int)]
    else:
        raise ValueError(conf)
    return df, y

def train_predict_save(conf, train, test, X_all_train, X_test):
    t0 = time.time()
    df, y = task_dataframe(train, conf)
    # Use original row ids to index precomputed features.
    row_ids = df["Unnamed: 0"].to_numpy()
    X = X_all_train[row_ids]

    log(f"\n=== {conf} ===")
    log("Rows:", X.shape[0], "Features:", X.shape[1], "Class counts:", dict(zip(*np.unique(y, return_counts=True))))
    log("Concern counts:", df["vDILIConcern"].value_counts().to_dict())

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    rf = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced_subsample",
        bootstrap=True,
    )
    # Compact but genuine search over the requested RF hyperparameter types.
    param_grid = {
        "n_estimators": [100, 250],
        "max_depth": [None, 16],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
        "max_features": ["sqrt"],
    }
    grid = GridSearchCV(
        rf,
        param_grid=param_grid,
        scoring="balanced_accuracy",
        cv=cv,
        n_jobs=-1,
        refit=True,
        verbose=0,
        return_train_score=False,
    )
    grid.fit(X, y)
    log("Best params:", grid.best_params_)
    log("Best 5-fold CV balanced accuracy:", round(float(grid.best_score_), 6))

    res = pd.DataFrame(grid.cv_results_).sort_values("rank_test_score").head(5)
    log("Top search results:")
    log(res[["rank_test_score", "mean_test_score", "std_test_score", "params"]].to_string(index=False))

    pred = grid.best_estimator_.predict(X_test)
    out = pd.DataFrame({
        "standardised_smiles": test["standardised_smiles"],
        "label": np.where(pred == 1, "DILI", "NoDILI")
    })
    out_path = os.path.join(OUT_DIR, f"{conf}_RF.csv")
    out.to_csv(out_path, index=False)
    log("Saved:", out_path, "shape:", out.shape, "label counts:", out["label"].value_counts().to_dict(),
        "elapsed_sec:", round(time.time() - t0, 2))
    log(out.head().to_string(index=False))
    return out_path

def main():
    t_all = time.time()
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    log("Loaded train/test:", train.shape, test.shape)
    log("Training concern counts:", train["vDILIConcern"].value_counts().to_dict())
    log("Split counts:", {
        "MC": train.iloc[0:173]["vDILIConcern"].value_counts().to_dict(),
        "LC": train.iloc[173:433]["vDILIConcern"].value_counts().to_dict(),
        "NC": train.iloc[433:660]["vDILIConcern"].value_counts().to_dict(),
        "sider": train.iloc[660:923]["vDILIConcern"].value_counts().to_dict(),
    })

    log("Featurizing train and test with Morgan fingerprints...")
    X_all_train = featurize(train["standardised_smiles"])
    X_test = featurize(test["standardised_smiles"])
    log("Feature matrices:", X_all_train.shape, X_test.shape)

    saved = []
    for conf in ["MCNC", "MCLCNC", "all"]:
        saved.append(train_predict_save(conf, train, test, X_all_train, X_test))

    log("\nDONE in seconds:", round(time.time() - t_all, 2))
    log("Saved files:", saved)
    log("pred_results listing:", sorted(os.listdir(OUT_DIR)))

if __name__ == "__main__":
    main()