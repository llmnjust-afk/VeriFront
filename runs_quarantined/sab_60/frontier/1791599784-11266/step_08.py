#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

root=Path("benchmark/datasets/nvc")

# Print concise complete rule sources (first enough; files are small) and missing combos
acc=pd.read_csv(root/"accuracies_data_for_plot.csv")
valid=pd.read_csv(root/"valid_syllogisms.csv")
print("Existing acc shape", acc.shape)
print("Columns", list(acc.columns))
print("Rules", sorted(acc.nvc.unique()))
print("Models", sorted(acc.model.unique()))
print("duplicate model/rule/task", acc.duplicated(["model","nvc","task"]).sum())
tasks=set(valid.syllog)
missing=[]
for m in sorted(acc.model.unique()):
    for r in sorted(acc.nvc.unique()):
        have=set(acc[(acc.model==m)&(acc.nvc==r)].task)
        if tasks-have:
            missing.append((m,r,sorted(tasks-have)))
print("Missing combos count", len(missing))
print(missing)

# Derive MFA truth from Ragni2016 to compare with existing truth.
rag=pd.read_csv(root/"Ragni2016.csv")
def quant_code(q):
    return {"All":"A", "Some":"I", "Some not":"O", "No":"E"}[q]
def figure_from_premises(p1, p2):
    # Syllogistic task code uses mood + figure, where conclusion terms are end terms a,c
    # Premises are categorical strings Q;subj;obj. Shared middle term is b.
    q1,s1,o1=p1.split(";")
    q2,s2,o2=p2.split(";")
    terms=[s1,o1,s2,o2]
    mid=[t for t in set(terms) if terms.count(t)==2][0]
    ends=[t for t in terms if t!=mid]
    # choices contain conclusion terms in canonical order for this item
    # infer a,c by positions:
    # fig1: b-a / c-b ; fig2: a-b / c-b ; fig3: b-a / b-c ; fig4: a-b / b-c
    if s1==mid and o2==mid:
        return "1"
    if o1==mid and o2==mid:
        return "2"
    if s1==mid and s2==mid:
        return "3"
    if o1==mid and s2==mid:
        return "4"
    raise ValueError((p1,p2,mid))
def task_code(task):
    p1,p2=task.split("/")
    return quant_code(p1.split(";")[0]) + quant_code(p2.split(";")[0]) + figure_from_premises(p1,p2)
def answer_code(row):
    resp=row["response"]
    if resp=="NVC":
        return "NVC"
    q,s,o=resp.split(";")
    qcode=quant_code(q)
    # Determine a/c order from choices: all choice terms are two end terms in both orders.
    first_choice=row["choices"].split("|")[0]
    _, a_term, c_term = first_choice.split(";")
    suffix = "ac" if (s==a_term and o==c_term) else "ca" if (s==c_term and o==a_term) else "??"
    return qcode+suffix
rag["syllog"]=rag["task"].map(task_code)
rag["answer_code"]=rag.apply(answer_code, axis=1)
mfa = (rag.groupby("syllog")["answer_code"]
       .agg(lambda s: s.value_counts().sort_values(ascending=False).index[0])
       .rename("mfa_truth").reset_index())
truth_existing=acc[["task","truth"]].drop_duplicates().rename(columns={"task":"syllog"})
cmp=truth_existing.merge(mfa,on="syllog",how="outer")
cmp["match"]=cmp["truth"].eq(cmp["mfa_truth"])
print("MFA comparison rows", cmp.shape, "matches", cmp["match"].sum(), "mismatches", (~cmp["match"]).sum())
print("Mismatches:")
print(cmp[~cmp["match"]].to_string(index=False))

# Print mean summaries to guide final output.
summary=(acc.groupby(["model","nvc"], as_index=False)
         .agg(model_accuracy=("hit_model","mean"),
              nvc_accuracy=("hit_nvc","mean"),
              mean_improvement=("improvement","mean"),
              n_tasks=("task","count")))
print("Summary head/all:")
print(summary.round(4).to_string(index=False))

# Inspect top-level scripts if any.
for py in sorted((root/"scripts").rglob("*.py")):
    if py.name != "__init__.py":
        txt=py.read_text()
        defs=[ln for ln in txt.splitlines() if ln.strip().startswith("def ") or ln.strip().startswith("class ")]
        print("PY", py.relative_to(root), "defs", defs, "size", py.stat().st_size)