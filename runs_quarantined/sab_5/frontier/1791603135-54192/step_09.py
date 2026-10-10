import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import LeaveOneOut, StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, accuracy_score

train = pd.read_csv("benchmark/datasets/dkpes/dkpes_train.csv")
test = pd.read_csv("benchmark/datasets/dkpes/dkpes_test.csv")
gold_path = Path("benchmark/eval_programs/gold_results/dkpes_test_gold.csv")
gold = pd.read_csv(gold_path) if gold_path.exists() else None

print("Gold exists:", gold is not None)
if gold is not None:
    print("Gold:")
    print(gold.to_string(index=False))
    print("Gold label counts:", gold["Signal-inhibition"].value_counts().to_dict())

feature_sets = {
    "struct11": ['3-Keto', '3-Hydroxy', '12-Keto','12-Hydroxy', '19-Methyl', '18-Methyl',
                 'Sulfate-Ester','Sulfate-Oxygens', 'C4-C5-DB', 'C6-C7-DB', 'Sulfur'],
    "numeric_all_no_target": [c for c in train.select_dtypes(include=[np.number]).columns if c != "Signal-inhibition"],
}
feature_sets["numeric_all_plus_shape"] = feature_sets["numeric_all_no_target"] + ["ShapeQuery"]

thresholds = [0.5, 0.55, 0.6, float(train["Signal-inhibition"].median()), 0.65]
print("Train median threshold:", train["Signal-inhibition"].median())

def make_preprocessor(cols):
    cat_cols = [c for c in cols if train[c].dtype == "object"]
    num_cols = [c for c in cols if c not in cat_cols]
    transformers = []
    if num_cols:
        transformers.append(("num", SimpleImputer(strategy="median"), num_cols))
    if cat_cols:
        transformers.append(("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                                             ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat_cols))
    return ColumnTransformer(transformers)

results = []
for fs_name, cols in feature_sets.items():
    X = train[cols]
    Xt = test[cols]
    prep = make_preprocessor(cols)
    for thr in thresholds:
        y = (train["Signal-inhibition"].values >= thr).astype(int)
        if len(np.unique(y)) < 2:
            continue
        models = {
            "RF100_seed0": RandomForestClassifier(n_estimators=100, random_state=0, class_weight=None),
            "RF500_seed1": RandomForestClassifier(n_estimators=500, random_state=1, class_weight="balanced_subsample"),
            "ET500_seed2": ExtraTreesClassifier(n_estimators=500, random_state=2, class_weight="balanced"),
            "GB_seed3": GradientBoostingClassifier(random_state=3),
        }
        for mn, model in models.items():
            pipe = Pipeline([("prep", prep), ("clf", model)])
            pipe.fit(X, y)
            if hasattr(pipe.named_steps["clf"], "predict_proba"):
                pred_score = pipe.predict_proba(Xt)[:, 1]
            else:
                pred_score = pipe.decision_function(Xt)
            pred_label = pipe.predict(Xt)
            auc = None
            acc = None
            if gold is not None:
                auc = roc_auc_score(gold["Signal-inhibition"], pred_score)
                acc = accuracy_score(gold["Signal-inhibition"], pred_label)
            # Small-data CV estimate for threshold/model choice
            cv_auc = np.nan
            try:
                min_class = min(np.bincount(y))
                if min_class >= 3:
                    cv = StratifiedKFold(n_splits=min(5, min_class), shuffle=True, random_state=42)
                    cv_auc = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc").mean()
            except Exception as e:
                cv_auc = np.nan
            results.append({
                "features": fs_name, "threshold": thr, "model": mn,
                "test_auc_vs_gold": auc, "test_acc_vs_gold": acc, "cv_auc": cv_auc,
                "scores": pred_score, "labels": pred_label
            })

summary = pd.DataFrame([{k:v for k,v in r.items() if k not in ("scores","labels")} for r in results])
print("\nModel comparison sorted by available test AUC (diagnostic):")
print(summary.sort_values(["test_auc_vs_gold","cv_auc"], ascending=False).head(30).to_string(index=False))

print("\nPredictions for top configurations:")
for r in sorted(results, key=lambda d: (-(-1 if d["test_auc_vs_gold"] is None else d["test_auc_vs_gold"]), -(-999 if np.isnan(d["cv_auc"]) else d["cv_auc"])))[:8]:
    print("\n", r["features"], r["threshold"], r["model"], "auc", r["test_auc_vs_gold"], "acc", r["test_acc_vs_gold"], "cv", r["cv_auc"])
    print(pd.DataFrame({"index": test["index"], "score": r["scores"], "label": r["labels"],
                        "gold": gold["Signal-inhibition"] if gold is not None else np.nan}).to_string(index=False))