#!/usr/bin/env python3
import os
import time
import warnings
import numpy as np
import pandas as pd

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import balanced_accuracy_score, accuracy_score, roc_auc_score, make_scorer

warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_STATE = 42
TRAIN_PATH = "benchmark/datasets/dili/train.csv"
TEST_PATH = "benchmark/datasets/dili/test.csv"
OUT_DIR = "pred_results"
os.makedirs(OUT_DIR, exist_ok=True)

def smiles_to_morgan(smiles, n_bits=2048, radius=2):
    """Return Morgan bit vector as uint8 numpy array; all-zero if parsing fails."""
    arr = np.zeros((n_bits,), dtype=np.uint8)
    if not isinstance(smiles, str) or not smiles.strip():
        return arr
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return arr
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def featurize(smiles_series, n_bits=2048, radius=2):
    X = np.vstack([smiles_to_morgan(s, n_bits=n_bits, radius=radius) for s in smiles_series])
    return X

def task_dataframe(train, conf):
    # Dataset split definitions are 1-based in the problem statement:
    # MC 1-173, LC 174-433, NC 434-660, sider 661-923.
    mc = train.iloc[0:173].copy()
    lc = train.iloc[173:433].copy()
    nc = train.iloc[433:660].copy()
    sider = train.iloc[660:923].copy()

    if conf == "MCNC":
        df = pd.concat([mc, nc], ignore_index=True)
        y = np.array([1] * len(mc) + [0] * len(nc), dtype=int)
    elif conf == "MCLCNC":
        pos = pd.concat([mc, lc], ignore_index=True)
        df = pd.concat([pos, nc], ignore_index=True)
        y = np.array([1] * len(pos) + [0] * len(nc), dtype=int)
    elif conf == "all":
        pos = pd.concat([mc, lc], ignore_index=True)
        neg = pd.concat([nc, sider], ignore_index=True)
        df = pd.concat([pos, neg], ignore_index=True)
        y = np.array([1] * len(pos) + [0] * len(neg), dtype=int)
    else:
        raise ValueError(conf)
    return df, y

def run_task(conf, train, test, X_test):
    t0 = time.time()
    df, y = task_dataframe(train, conf)
    X = featurize(df["standardised_smiles"])
    print(f"\n=== {conf} ===")
    print("training rows:", len(df), "features:", X.shape[1], "class counts:", dict(zip(*np.unique(y, return_counts=True))))
    print("vDILIConcern counts used:", df["vDILIConcern"].value_counts().to_dict())

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    rf = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced_subsample",
        bootstrap=True,
    )
    param_grid = {
        "n_estimators": [200, 500],
        "max_depth": [None, 10, 20],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
        "max_features": ["sqrt", None],
    }
    grid = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        scoring="balanced_accuracy",
        cv=cv,
        n_jobs=-1,
        refit=True,
        verbose=0,
        return_train_score=True,
    )
    grid.fit(X, y)

    print("best params:", grid.best_params_)
    print("best mean CV balanced_accuracy:", round(float(grid.best_score_), 6))

    # Summarize top few CV configurations.
    res = pd.DataFrame(grid.cv_results_).sort_values("rank_test_score").head(5)
    cols = ["rank_test_score", "mean_test_score", "std_test_score", "mean_train_score", "params"]
    print("top CV rows:")
    print(res[cols].to_string(index=False))

    best_model = grid.best_estimator_
    pred = best_model.predict(X_test)
    labels = np.where(pred == 1, "DILI", "NoDILI")
    out = pd.DataFrame({
        "standardised_smiles": test["standardised_smiles"],
        "label": labels,
    })
    out_path = os.path.join(OUT_DIR, f"{conf}_RF.csv")
    out.to_csv(out_path, index=False)
    print("test prediction counts:", out["label"].value_counts().to_dict())
    print("saved:", out_path, "shape:", out.shape, "elapsed_sec:", round(time.time() - t0, 2))
    print("preview:")
    print(out.head(10).to_string(index=False))
    return out_path

def main():
    print("Loading:", TRAIN_PATH, TEST_PATH)
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    print("train shape:", train.shape, "test shape:", test.shape)
    print("train columns:", list(train.columns))
    print("test columns:", list(test.columns))
    print("overall vDILIConcern counts:", train["vDILIConcern"].value_counts().to_dict())

    # Check split boundaries against stated labels.
    split_summaries = {
        "MC_1_173": train.iloc[0:173]["vDILIConcern"].value_counts().to_dict(),
        "LC_174_433": train.iloc[173:433]["vDILIConcern"].value_counts().to_dict(),
        "NC_434_660": train.iloc[433:660]["vDILIConcern"].value_counts().to_dict(),
        "sider_661_923": train.iloc[660:923]["vDILIConcern"].value_counts().to_dict(),
    }
    print("split summaries:", split_summaries)

    X_test = featurize(test["standardised_smiles"])
    print("X_test shape:", X_test.shape, "nonzero bit counts first five:", X_test[:5].sum(axis=1).tolist())

    saved = []
    for conf in ["MCNC", "MCLCNC", "all"]:
        saved.append(run_task(conf, train, test, X_test))

    print("\nDONE. Saved files:", saved)
    print("pred_results listing:", os.listdir(OUT_DIR))

if __name__ == "__main__":
    main()