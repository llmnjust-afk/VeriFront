#!/usr/bin/env python3
import os, inspect
import pandas as pd
from biopsykit.questionnaires import pss

path = "benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl"
df = pd.read_pickle(path)
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]

print("BioPsyKit pss source:")
print(inspect.getsource(pss))

print("Default pss output:")
try:
    out_default = pss(df, columns=pss_cols)
    print(type(out_default), out_default.shape)
    print(out_default.to_string())
except Exception as e:
    print("Default pss failed:", repr(e))

print("PSS without columns:")
try:
    out_no_cols = pss(df[pss_cols])
    print(type(out_no_cols), out_no_cols.shape)
    print(out_no_cols.to_string())
except Exception as e:
    print("No cols failed:", repr(e))

# Try likely subscale definitions if needed.
subscales = {
    "Perceived Helplessness": ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"],
    "Perceived Self-Efficacy": ["PSS_04", "PSS_05", "PSS_07", "PSS_08"],
}
print("Custom subscales pss output:")
try:
    out_sub = pss(df, columns=pss_cols, subscales=subscales)
    print(type(out_sub), out_sub.shape)
    print(out_sub.to_string())
except Exception as e:
    print("Custom subscales failed:", repr(e))