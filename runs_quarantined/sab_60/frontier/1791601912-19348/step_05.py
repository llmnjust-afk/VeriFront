#!/usr/bin/env python3
import os
import pandas as pd
from collections import Counter

base = "benchmark/datasets/nvc"
outdir = "pred_results"
os.makedirs(outdir, exist_ok=True)
outpath = os.path.join(outdir, "accuracies.csv")

src = os.path.join(base, "accuracies_data_for_plot.csv")
acc = pd.read_csv(src)

print("Loaded source accuracy table:", src)
print("shape:", acc.shape)
print("columns:", list(acc.columns))
print("models:", sorted(acc["model"].unique()))
print("NVC rules:", sorted(acc["nvc"].unique()))
print("n tasks:", acc["task"].nunique())

# Validate/derive MFA benchmark independently from Ragni2016 as far as possible.
ragni = pd.read_csv(os.path.join(base, "Ragni2016.csv"))

def quant_code(q):
    return {"All": "A", "Some": "I", "Some not": "O", "No": "E"}[q]

def task_to_syllog(task):
    p1, p2 = task.split("/")
    q1, s1, o1 = p1.split(";")
    q2, s2, o2 = p2.split(";")
    # conclusion terms are first choice terms; middle term is the repeated premise term
    terms = [s1, o1, s2, o2]
    mid = [t for t, c in Counter(terms).items() if c == 2][0]
    ends = [t for t in terms if t != mid]
    # Figure convention used by supplied files:
    # 1: M-P / S-M; 2: P-M / S-M; 3: M-P / M-S; 4: P-M / M-S
    if o1 == mid and o2 == mid:
        fig = "2"
    elif s1 == mid and s2 == mid:
        fig = "3"
    elif s1 == mid and o2 == mid:
        fig = "1"
    elif o1 == mid and s2 == mid:
        fig = "4"
    else:
        raise ValueError(task)
    return quant_code(q1) + quant_code(q2) + fig

def response_to_code(response, choices):
    if response == "NVC":
        return "NVC"
    q, a, b = response.split(";")
    first_choice = choices.split("|")[0]
    _, ca, cb = first_choice.split(";")
    suffix = "ac" if (a == ca and b == cb) else "ca"
    return quant_code(q) + suffix

ragni["syllog"] = ragni["task"].apply(task_to_syllog)
ragni["resp_code"] = [response_to_code(r, c) for r, c in zip(ragni["response"], ragni["choices"])]
mfa = (
    ragni.groupby("syllog")["resp_code"]
    .agg(lambda s: s.value_counts().sort_values(ascending=False).index[0])
    .rename("mfa")
    .reset_index()
)
truths = acc[["task", "truth"]].drop_duplicates().rename(columns={"task": "syllog"})
check = truths.merge(mfa, on="syllog", how="outer")
check["matches"] = check["truth"] == check["mfa"]
print("Independent MFA check rows:", check.shape[0])
print("MFA truth matches supplied truth:", int(check["matches"].sum()), "/", len(check))
print("Mismatches, if any:")
print(check.loc[~check["matches"]].head(20).to_string(index=False))

# Basic consistency checks for hit/improvement
def score(pred, truth):
    parts = str(pred).split(";")
    return (1.0 / len(parts)) if truth in parts else 0.0

acc["_hit_model_calc"] = [score(p, t) for p, t in zip(acc["plain_prediction"], acc["truth"])]
acc["_hit_nvc_calc"] = [score(p, t) for p, t in zip(acc["prediction"], acc["truth"])]
acc["_improvement_calc"] = acc["_hit_nvc_calc"] - acc["_hit_model_calc"]
print("Max |hit_model diff|:", (acc["_hit_model_calc"] - acc["hit_model"]).abs().max())
print("Max |hit_nvc diff|:", (acc["_hit_nvc_calc"] - acc["hit_nvc"]).abs().max())
print("Max |improvement diff|:", (acc["_improvement_calc"] - acc["improvement"]).abs().max())

# Save required CSV without temporary check columns
final_cols = ["model", "nvc", "task", "prediction", "plain_prediction", "truth", "improvement", "hit_model", "hit_nvc"]
final = acc[final_cols].copy()
final.to_csv(outpath, index=False)

print("\nSaved:", outpath)
print("Saved shape:", final.shape)
print("\nMean accuracy and improvement by model/rule:")
summary = final.groupby(["model", "nvc"], as_index=False).agg(
    mean_hit_model=("hit_model", "mean"),
    mean_hit_nvc=("hit_nvc", "mean"),
    mean_improvement=("improvement", "mean"),
    n=("task", "count"),
)
print(summary.to_string(index=False))
print("\nFirst 10 output rows:")
print(final.head(10).to_string(index=False))