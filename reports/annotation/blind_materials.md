

===== POINT 1/38: t18s1@1791613049-280338 =====
[TASK-DESC] Feature Engineering, Machine Learning
[STEP-CODE t18 step 1] (7995 chars)
#!/usr/bin/env python3
"""
Train Random Forest DILI classifiers for MCNC, MCLCNC, and all configurations.
Outputs prediction CSVs under pred_results/{data_conf}_RF.csv with columns:
standardised_smiles,label
"""
import os
import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import make_scorer, balanced_accuracy_score, accuracy_score, roc_auc_score
from sklearn.feature_extraction.text import HashingVectorizer
from scipy import sparse

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
TRAIN_PATH = Path("dili/train.csv")
TEST_PATH = Path("dili/test.csv")
OUT_DIR = Path("pred_results")
OUT_DIR.mkdir(exist_ok=True)

print("Starting DILI Random Forest training workflow")
print(f"Python: {sys.version.split()[0]}")
print(f"Train path exists: {TRAIN_PATH.exists()} | Test path exists: {TEST_PATH.exists()}")

train_df = pd.read_csv(TRAIN_PATH)
test_df = pd.read_csv(TEST_PATH)

print(f"Loaded train shape: {train_df.shape}")
print(f"Loaded test shape: {test_df.shape}")
print(f"Train columns: {list(train_df.columns)}")
print(f"Test columns: {list(test_df.columns)}")
print("vDILIConcern counts:")
print(train_df["vDILIConcern"].value_counts(dropna=False).to_string())

# Try RDKit Morgan fingerprints; fallback to hashed character n-grams if RDKit is unavailable.
USE_RDKIT = False
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, DataStructs
    USE_RDKIT = True
    print("RDKit available: using Morgan fingerprints.")
except Exception as e:
    print(f"RDKit unavailable ({repr(e)}): using hashed SMILES character n-gram features fallback.")

def morgan_features(smiles_list, n_bits=2048, radius=2):
    arr = np.zeros((len(smiles_list), n_bits), dtype=np.uint8)
    invalid = []
    for i, smi in enumerate(smiles_list):
        if not isinstance(smi, str) or not smi.strip():
            invalid.append((i, smi))
            continue
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            invalid.append((i, smi))
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        DataStructs.ConvertToNumpyArray(fp, arr[i])
    if invalid:
        print(f"Warning: {len(invalid)} invalid/empty SMILES featurized as zero vector. First few: {invalid[:5]}")
    return arr

def hashed_smiles_features(train_smiles, test_smiles, n_features=4096):
    vec = HashingVectorizer(
        analyzer="char",
        ngram_range=(2,
[OBS t18 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Starting DILI Random Forest training workflow | Python: 3.10.22 | Train path exists: True | Test path exists: True | Loaded train shape: (923, 6) | Loaded test shape: (55, 1) | Train columns: ['Unnamed: 0', 'PubChem_CID', 'Compound Name', 'standardised_smiles', 'vDILIConcern', 'cluster'] | Test columns: ['standardised_smiles'] | vDILIConcern counts: | vDILIConcern | sider_inactive        262 | vLess-DILI-Concern    260 | vNo-DILI-Concern      227 | vMost-DILI-Concern    174 | RDKit available: 


===== POINT 2/38: t18s1@1791614252-322475 =====
[TASK-DESC] Feature Engineering, Machine Learning
[STEP-CODE t18 step 1] (1040 chars)
#!/usr/bin/env python3
import os
import sys
import json
import importlib.util
from pathlib import Path

print("Working directory:", os.getcwd())
print("Python:", sys.version)

for pkg in ["pandas", "numpy", "sklearn", "rdkit"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}: {'FOUND' if spec else 'MISSING'}")

data_dir = Path("dili")
print("Data dir exists:", data_dir.exists())
for fn in ["train.csv", "test.csv"]:
    p = data_dir / fn
    print(f"\nFile {p}: exists={p.exists()} size={p.stat().st_size if p.exists() else 'NA'}")
    if p.exists():
        import pandas as pd
        df = pd.read_csv(p)
        print(f"{fn} shape:", df.shape)
        print(f"{fn} columns:", list(df.columns))
        print(df.head().to_string())
        if "vDILIConcern" in df.columns:
            print("vDILIConcern counts:")
            print(df["vDILIConcern"].value_counts(dropna=False).to_string())
        if "standardised_smiles" in df.columns:
            print("Missing smiles:", df["standardised_smiles"].isna().sum())
[OBS t18 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Working directory: /tmp/vf_work/sab_18/frontier/acba6380a92a/wd | Python: 3.10.22 | packaged by conda-forge | (main, Oct  6 2026, 23:02:24) [GCC 14.4.0] | Package pandas: FOUND | Package numpy: FOUND | Package sklearn: FOUND | Package rdkit: FOUND | Data dir exists: True |  | File dili/train.csv: exists=True size=80524 | train.csv shape: (923, 6) | train.csv columns: ['Unnamed: 0', 'PubChem_CID', 'Compound Name', 'standardised_smiles', 'vDILIConcern', 'cluster'] |    Unnamed: 0  PubChem_CI


===== POINT 3/38: t18s2@1791614252-322475 =====
[TASK-DESC] Feature Engineering, Machine Learning
[STEP-CODE t18 step 2] (1570 chars)
#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

train = pd.read_csv("dili/train.csv")
print("Train shape", train.shape)

# Inspect label transitions and the benchmark's stated split boundaries.
print("\nRows around stated 1-based boundaries:")
for start, end in [(165,180), (425,440), (652,668)]:
    print(f"\n0-based rows {start}:{end}")
    cols = ["Unnamed: 0", "Compound Name", "vDILIConcern"]
    print(train.loc[start:end, cols].to_string(index=True))

print("\nCounts in likely 0-based contiguous concern blocks (by label run):")
# identify runs
runs = []
current = None
run_start = 0
for i, val in enumerate(train["vDILIConcern"]):
    if i == 0:
        current = val
    elif val != current:
        runs.append((run_start, i-1, current, i-run_start))
        run_start = i
        current = val
runs.append((run_start, len(train)-1, current, len(train)-run_start))
for r in runs:
    print(r)

print("\nCounts by stated 1-based splits converted to 0-based inclusive:")
splits = {
    "MC_1_173": (0,172),
    "LC_174_433": (173,432),
    "NC_434_660": (433,659),
    "sider_661_923": (660,922),
}
for name, (a,b) in splits.items():
    vc = train.iloc[a:b+1]["vDILIConcern"].value_counts()
    print(name, a, b, b-a+1)
    print(vc.to_string())

print("\nCounts by natural label runs:")
for name, lab in [("MC", "vMost-DILI-Concern"), ("LC", "vLess-DILI-Concern"), ("NC", "vNo-DILI-Concern"), ("sider", "sider_inactive")]:
    idx = train.index[train["vDILIConcern"] == lab]
    print(name, lab, len(idx), int(idx.min()), int(idx.max()))
[OBS t18 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- | Train shape (923, 6) |  | Rows around stated 1-based boundaries: |  | 0-based rows 165:180 |      Unnamed: 0   Compound Name        vDILIConcern | 165         165     terbinafine  vMost-DILI-Concern | 166         166    testosterone  vMost-DILI-Concern | 167         167   thiabendazole  vMost-DILI-Concern | 168         168     ticlopidine  vMost-DILI-Concern | 169         169      tizanidine  vMost-DILI-Concern | 170         170       tolvaptan  vMost-DILI-Concern | 171         171    vorico


===== POINT 4/38: t18s3@1791614252-322475 =====
[TASK-DESC] Feature Engineering, Machine Learning
[STEP-CODE t18 step 3] (5608 chars)
#!/usr/bin/env python3
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, DataStructs
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import balanced_accuracy_score, accuracy_score, f1_score, roc_auc_score, make_scorer

RDLogger.DisableLog("rdApp.*")
warnings.filterwarnings("ignore")

RANDOM_STATE = 42
FP_BITS = 2048
FP_RADIUS = 2

out_dir = Path("pred_results")
out_dir.mkdir(exist_ok=True)

train_path = Path("dili/train.csv")
test_path = Path("dili/test.csv")
train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

print("Loaded train:", train.shape, "test:", test.shape)
print("Train label counts:")
print(train["vDILIConcern"].value_counts().to_string())

def smiles_to_morgan_array(smiles_list, n_bits=FP_BITS, radius=FP_RADIUS):
    X = np.zeros((len(smiles_list), n_bits), dtype=np.uint8)
    bad = []
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(str(smi))
        if mol is None:
            bad.append((i, smi))
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        DataStructs.ConvertToNumpyArray(fp, X[i])
    return X, bad

# Featurize all unique needed rows once.
X_train_all, bad_train = smiles_to_morgan_array(train["standardised_smiles"].tolist())
X_test, bad_test = smiles_to_morgan_array(test["standardised_smiles"].tolist())
print(f"Fingerprints: train {X_train_all.shape}, test {X_test.shape}")
print(f"Invalid train SMILES: {len(bad_train)}; invalid test SMILES: {len(bad_test)}")
if bad_train[:5]:
    print("First invalid train examples:", bad_train[:5])
if bad_test[:5]:
    print("First invalid test examples:", bad_test[:5])

# Use the actual contiguous label-defined blocks in this provided file.
# They correspond to MC=vMost, LC=vLess, NC=vNo, sider=sider_inactive.
label_sets = {
    "MCNC": {
        "positive": ["vMost-DILI-Concern"],
        "negative": ["vNo-DILI-Concern"],
    },
    "MCLCNC": {
        "positive": ["vMost-DILI-Concern", "vLess-DILI-Concern"],
        "negative": ["vNo-DILI-Concern"],
    },
    "all": {
        "positive": ["vMost-DILI-Concern", "vLess-DILI-Concern"],
        "negative": ["vNo-DILI-Concern", "sider_inactive"],
    },
}

param_grid = {
    "n_estimators": [200, 500],
    "max_depth": [None, 10, 20],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [1, 2],
    "max_features": ["sqrt"],
}

cv = StratifiedKFold(n_splits=5, sh
[OBS t18 step 3 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded train: (923, 6) test: (55, 1) | Train label counts: | vDILIConcern | sider_inactive        262 | vLess-DILI-Concern    260 | vNo-DILI-Concern      227 | vMost-DILI-Concern    174 | Fingerprints: train (923, 2048), test (55, 2048) | Invalid train SMILES: 0; invalid test SMILES: 0 |  | ================================================================================ | Configuration: MCNC | Training rows: 401 Positive(DILI): 174 Negative(NoDILI): 227 | Included labels: | vDILIConcern | vNo-DILI


===== POINT 5/38: t34s1@1791612856-279147 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t34 step 1] (14931 chars)
#!/usr/bin/env python3
"""
Compute HRV features from biosignals/bio_resting_5min_100hz.csv and save to
pred_results/hrv_analysis_pred.csv.

The script prefers NeuroKit2 if available, and otherwise uses a scipy/numpy
implementation for ECG cleaning, R-peak detection, and HRV time/frequency/
nonlinear features.
"""
import os
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

DATA_PATH = Path("biosignals/bio_resting_5min_100hz.csv")
OUT_DIR = Path("pred_results")
OUT_PATH = OUT_DIR / "hrv_analysis_pred.csv"
FS = 100.0


def _as_scalar(x):
    try:
        if hasattr(x, "iloc"):
            return x.iloc[0]
        if isinstance(x, (list, tuple, np.ndarray)):
            return x[0]
        return x
    except Exception:
        return x


def _sanitize_features(d):
    out = {}
    for k, v in d.items():
        val = _as_scalar(v)
        try:
            val = float(val)
            if not np.isfinite(val):
                val = np.nan
        except Exception:
            continue
        out[str(k)] = val
    return out


def try_neurokit(ecg, fs):
    """Return feature dictionary and R-peak samples using NeuroKit2, or (None, None)."""
    try:
        import neurokit2 as nk
    except Exception as exc:
        print(f"NeuroKit2 not available, using fallback implementation. Import error: {exc}")
        return None, None

    try:
        ecg_cleaned = nk.ecg_clean(ecg, sampling_rate=int(fs), method="neurokit")
        signals, info = nk.ecg_peaks(ecg_cleaned, sampling_rate=int(fs), method="neurokit", correct_artifacts=True)
        peaks = np.asarray(info.get("ECG_R_Peaks", []), dtype=int)
        if len(peaks) < 5:
            raise RuntimeError(f"NeuroKit2 detected too few peaks: {len(peaks)}")

        time_df = nk.hrv_time(peaks, sampling_rate=int(fs), show=False)
        freq_df = nk.hrv_frequency(peaks, sampling_rate=int(fs), show=False, normalize=False)
        nonlin_df = nk.hrv_nonlinear(peaks, sampling_rate=int(fs), show=False)

        features = {}
        features.update(_sanitize_features(time_df.iloc[0].to_dict()))
        features.update(_sanitize_features(freq_df.iloc[0].to_dict()))
        features.update(_sanitize_features(nonlin_df.iloc[0].to_dict()))

        # Add explicit simple provenance/count features.
        features["RPeak_Count"] = float(len(peaks))
        features["Recording_Duration_s"] = float(len(ecg) / fs)
        features["Mean_HR_bpm_from_peaks"] = float(60.0 / np.mean(np.diff(peaks) / fs))

        print("Used NeuroKit2 implementation.")
[OBS t34 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded biosignals/bio_resting_5min_100hz.csv: rows=29900, columns=['ECG', 'PPG', 'RSP'], duration=299.00s | ECG summary: mean=-0.00708476, std=0.0411407, min=-0.708476, max=0.894532 | Used NeuroKit2 implementation. | Detected R peaks: 432 | Valid RR intervals: 431 | RR mean=692.436 ms, SDNN=48.841 ms, HR=86.651 bpm | Saved 94 HRV/provenance columns to pred_results/hrv_analysis_pred.csv | Output preview: |  Recording_Duration_s  RPeak_Count  Mean_HR_bpm_from_peaks    HRV_AI  HRV_ApEn 


===== POINT 6/38: t34s1@1791614163-321498 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t34 step 1] (852 chars)
import os
import sys
import importlib.util
import pandas as pd

print("Working directory:", os.getcwd())
print("Files in biosignals:", os.listdir("biosignals") if os.path.isdir("biosignals") else "MISSING")

path = "biosignals/bio_resting_5min_100hz.csv"
df = pd.read_csv(path)
print("Loaded:", path)
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print(df.head())
print(df.describe().T)

for pkg in ["neurokit2", "scipy", "numpy", "pandas"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}:", "available" if spec is not None else "not available")
    if spec is not None:
        try:
            mod = importlib.import_module(pkg)
            print(f"  version: {getattr(mod, '__version__', 'unknown')}")
        except Exception as e:
            print(f"  import error: {e}")

print("Initial inspection complete.")
[OBS t34 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Working directory: /tmp/vf_work/sab_34/frontier/3f913fbfdc67/wd | Files in biosignals: ['eog_100hz.csv', 'ecg_1000hz.csv', 'bio_resting_5min_100hz.csv', 'bio_eventrelated_100hz.csv'] | Loaded: biosignals/bio_resting_5min_100hz.csv | Shape: (29900, 3) | Columns: ['ECG', 'PPG', 'RSP'] |         ECG       PPG       RSP | 0  0.003766 -0.102539  0.494652 | 1 -0.017466 -0.103760  0.502483 | 2 -0.015679 -0.107422  0.511102 | 3 -0.001598 -0.110855  0.518791 | 4  0.002483 -0.112610  0.528669 |     


===== POINT 7/38: t34s2@1791614163-321498 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t34 step 2] (2572 chars)
import os
import warnings
import numpy as np
import pandas as pd
import neurokit2 as nk

warnings.filterwarnings("ignore")
os.makedirs("pred_results", exist_ok=True)

input_path = "biosignals/bio_resting_5min_100hz.csv"
output_path = "pred_results/hrv_analysis_pred.csv"
sampling_rate = 100

df = pd.read_csv(input_path)
ecg = df["ECG"].astype(float).to_numpy()

print("Loaded ECG samples:", len(ecg), "duration_s:", len(ecg) / sampling_rate)

# Clean ECG and detect R-peaks using NeuroKit2.
ecg_cleaned = nk.ecg_clean(ecg, sampling_rate=sampling_rate, method="neurokit")
signals, info = nk.ecg_peaks(ecg_cleaned, sampling_rate=sampling_rate, method="neurokit", correct_artifacts=True)
rpeaks = np.asarray(info["ECG_R_Peaks"], dtype=int)

print("Detected R-peaks:", len(rpeaks))
print("First 10 R-peaks samples:", rpeaks[:10].tolist())
rr_ms = np.diff(rpeaks) / sampling_rate * 1000
print("RR interval ms summary:")
print(pd.Series(rr_ms).describe())

# Compute HRV indices from three domains.
hrv_time = nk.hrv_time(rpeaks, sampling_rate=sampling_rate, show=False)
hrv_freq = nk.hrv_frequency(rpeaks, sampling_rate=sampling_rate, show=False, normalize=True)
hrv_nonlinear = nk.hrv_nonlinear(rpeaks, sampling_rate=sampling_rate, show=False)

print("Time-domain feature shape:", hrv_time.shape)
print("Frequency-domain feature shape:", hrv_freq.shape)
print("Nonlinear-domain feature shape:", hrv_nonlinear.shape)

# Add explicit prefixes only if needed? NeuroKit columns already start HRV_.
# Concatenate into one-row feature table.
features = pd.concat(
    [
        hrv_time.reset_index(drop=True),
        hrv_freq.reset_index(drop=True),
        hrv_nonlinear.reset_index(drop=True),
    ],
    axis=1,
)

# Remove duplicate columns if any, preserving first occurrence.
features = features.loc[:, ~features.columns.duplicated()].copy()

# Include useful peak-count metadata while keeping HRV extracted features as main output.
features.insert(0, "ECG_R_Peaks_N", len(rpeaks))
features.insert(1, "ECG_R_Peaks_Rate_per_min", len(rpeaks) / (len(ecg) / sampling_rate / 60))

# Convert object/bool to numeric-friendly values where possible.
for col in features.columns:
    if features[col].dtype == bool:
        features[col] = features[col].astype(int)

features.to_csv(output_path, index=False)

print("Saved:", output_path)
print("Output shape:", features.shape)
print("Columns:")
print(list(features.columns))
print("Feature values preview:")
with pd.option_context("display.max_columns", 200, "display.width", 240):
    print(features.head().to_string(index=False))
[OBS t34 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded ECG samples: 29900 duration_s: 299.0 | Detected R-peaks: 432 | First 10 R-peaks samples: [49, 107, 167, 226, 285, 346, 407, 469, 538, 612] | RR interval ms summary: | count    431.000000 | mean     692.436195 | std       48.841033 | min      520.000000 | 25%      660.000000 | 50%      690.000000 | 75%      720.000000 | max      860.000000 | dtype: float64 | Time-domain feature shape: (1, 25) | Frequency-domain feature shape: (1, 10) | Nonlinear-domain feature shape: (1, 56) | Saved: pred_resu


===== POINT 8/38: t35s1@1791612654-276937 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t35 step 1] (16028 chars)
#!/usr/bin/env python3
import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from scipy import signal, interpolate, stats


def read_rsp(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    if "RSP" not in df.columns:
        raise ValueError(f"RSP column not found. Columns: {df.columns.tolist()}")
    rsp = pd.to_numeric(df["RSP"], errors="coerce").to_numpy(dtype=float)
    # Fill missing values by linear interpolation.
    if np.any(~np.isfinite(rsp)):
        s = pd.Series(rsp)
        rsp = s.interpolate(limit_direction="both").to_numpy(dtype=float)
    return rsp, df


def robust_bandpass(x, fs, low=0.05, high=1.0, order=4):
    """Clean respiration with a physiologically plausible bandpass."""
    x = np.asarray(x, dtype=float)
    x = x - np.nanmedian(x)
    nyq = fs / 2.0
    low = max(low, 0.001)
    high = min(high, nyq * 0.95)
    b, a = signal.butter(order, [low / nyq, high / nyq], btype="bandpass")
    # padlen guard for short signals
    if len(x) > max(len(a), len(b)) * 6:
        y = signal.filtfilt(b, a, x)
    else:
        y = signal.lfilter(b, a, x)
    return y


def detect_inhalation_peaks(cleaned_rsp, fs):
    """Detect inhalation peaks in the cleaned RSP waveform."""
    x = np.asarray(cleaned_rsp, dtype=float)
    # Smooth slightly to prevent high-frequency peak fragmentation.
    win = int(round(0.25 * fs))
    if win % 2 == 0:
        win += 1
    if win >= 5 and len(x) > win:
        xs = signal.savgol_filter(x, window_length=win, polyorder=3)
    else:
        xs = x.copy()

    # Estimate robust amplitude scale.
    mad = np.median(np.abs(xs - np.median(xs)))
    robust_sd = 1.4826 * mad if mad > 0 else np.std(xs)
    prom = max(0.15 * robust_sd, 0.03 * (np.percentile(xs, 95) - np.percentile(xs, 5)))

    # Respiratory peaks: normally no closer than ~1.2 s (50 breaths/min).
    distance = int(round(1.2 * fs))
    peaks, props = signal.find_peaks(xs, distance=distance, prominence=prom)

    # If too few peaks, relax prominence.
    if len(peaks) < 5:
        peaks, props = signal.find_peaks(xs, distance=distance, prominence=max(prom * 0.33, 1e-12))

    # Keep peaks that imply plausible neighbouring breath intervals where possible.
    if len(peaks) >= 3:
        t = peaks / fs
        intervals = np.diff(t)
        plausible = (intervals >= 1.0) & (intervals <= 12.0)
        keep = np.ones(len(peaks), dtype=bool)
        # A peak is retained if either interval adjacent to it is plausible.
        for i in range(len(peaks)):
            left = pl
[OBS t35 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Saved RRV analysis to: pred_results/rrv_analysis_pred.csv | Shape: (1, 53) | Key extracted values: |  duration_seconds  rsp_inhalation_peak_count  respiratory_rate_peak_count  rrv_breath_interval_count  rrv_mean_rate_bpm  rrv_sd_rate_bpm  rrv_rmssd_s  rrv_lf_power  rrv_hf_power  rrv_sample_entropy |             149.0                          0                            0                          0                NaN              NaN          NaN           NaN           NaN  


===== POINT 9/38: t35s1@1791613992-319454 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t35 step 1] (22322 chars)
#!/usr/bin/env python3
"""
RRV analysis for biosignals/bio_eventrelated_100hz.csv.

Outputs:
  pred_results/rrv_analysis_pred.csv

This script:
  1. Loads the RSP signal sampled at 100 Hz.
  2. Cleans the RSP signal with a respiration-band Butterworth filter.
  3. Extracts inhalation peaks from the cleaned RSP signal.
  4. Builds an instantaneous respiratory-rate signal and extracts its peaks.
  5. Computes respiratory-rate-variability indices:
     - Time domain
     - Frequency domain
     - Nonlinear / complexity
  6. Saves one row of features to the required CSV.
"""

import os
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from scipy import signal, interpolate, stats
from scipy.spatial import cKDTree


FS = 100.0
INPUT_PATH = Path("biosignals/bio_eventrelated_100hz.csv")
OUTPUT_PATH = Path("pred_results/rrv_analysis_pred.csv")


def _as_float_array(x):
    x = pd.to_numeric(pd.Series(x), errors="coerce").to_numpy(dtype=float)
    if np.any(~np.isfinite(x)):
        idx = np.arange(len(x))
        good = np.isfinite(x)
        if good.sum() == 0:
            raise ValueError("Signal contains no finite samples.")
        x[~good] = np.interp(idx[~good], idx[good], x[good])
    return x


def clean_rsp_rspband(rsp, fs):
    """Respiration-band cleaning: detrend + bandpass + light smoothing."""
    rsp = _as_float_array(rsp)

    # Remove slow linear trend and center.
    x = signal.detrend(rsp, type="linear")
    x = x - np.nanmedian(x)

    # Respiration band. Upper bound kept below Nyquist.
    low = 0.05
    high = 1.00
    nyq = fs / 2.0
    sos = signal.butter(4, [low / nyq, high / nyq], btype="bandpass", output="sos")
    cleaned = signal.sosfiltfilt(sos, x)

    # Very light smoothing to reduce small high-frequency extrema.
    win = int(round(0.25 * fs))
    if win % 2 == 0:
        win += 1
    if win >= 5 and win < len(cleaned):
        cleaned = signal.savgol_filter(cleaned, window_length=win, polyorder=2, mode="interp")

    return cleaned


def detect_inhalation_peaks(cleaned, fs):
    """Adaptive peak picking for inhalation maxima in cleaned respiration."""
    x = np.asarray(cleaned, dtype=float)
    robust_sd = 1.4826 * np.nanmedian(np.abs(x - np.nanmedian(x)))
    if not np.isfinite(robust_sd) or robust_sd <= 0:
        robust_sd = float(np.nanstd(x))
    if not np.isfinite(robust_sd) or robust_sd <= 0:
        robust_sd = 1.0

    # Try increasingly permissive settings until a plausible number is found.
    attempts = [
        dict(distance=1.50, prominence=0.25),
        dict(distance=1
[OBS t35 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded biosignals/bio_eventrelated_100hz.csv with shape (14900, 4) | Columns: ['ECG', 'EDA', 'Photosensor', 'RSP'] | Cleaned RSP length: 14900 samples | Detected inhalation peaks: 44 | Detected respiratory-rate signal peaks: 11 | Key RRV results: |   recording_duration_min: 2.4833333333333334 |   rsp_inhalation_peak_rate_per_min: 17.71812080536913 |   rsp_valid_interval_count: 41 |   rrv_mean_bbi_s: 3.2963414634146337 |   rrv_sd_bbi_s: 0.47216922865409805 |   rrv_rmssd_s: 0.565362715431435


===== POINT 10/38: t37s2@1791614063-319742 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t37 step 2] (1570 chars)
import importlib.util
import pkgutil
import inspect
from pathlib import Path

mods = ["biopsykit", "neurokit2", "heartpy"]
for m in mods:
    spec = importlib.util.find_spec(m)
    print(m, "installed:", spec is not None, "origin:", spec.origin if spec else None)

if importlib.util.find_spec("biopsykit"):
    import biopsykit
    print("biopsykit version:", getattr(biopsykit, "__version__", "unknown"))
    print("biopsykit path:", biopsykit.__path__)
    names = []
    for mod in pkgutil.walk_packages(biopsykit.__path__, biopsykit.__name__ + "."):
        if any(k in mod.name.lower() for k in ["cft", "cold", "mist", "hr"]):
            names.append(mod.name)
    print("candidate modules:", names[:200])
    for name in names:
        try:
            module = importlib.import_module(name)
            print("\nMODULE", name)
            for obj_name in dir(module):
                if any(k in obj_name.lower() for k in ["cft", "cold", "hr", "heart", "onset", "baseline"]):
                    obj = getattr(module, obj_name)
                    print(" ", obj_name, type(obj))
                    if inspect.isfunction(obj) or inspect.isclass(obj):
                        try:
                            print("   sig:", inspect.signature(obj))
                        except Exception:
                            pass
                        doc = inspect.getdoc(obj)
                        if doc:
                            print("   doc:", doc[:500].replace("\n", " "))
        except Exception as e:
            print("FAILED import", name, repr(e))
[OBS t37 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- | biopsykit installed: True origin: /root/.local/share/mamba/envs/testbed/lib/python3.10/site-packages/biopsykit/__init__.py | neurokit2 installed: True origin: /root/.local/share/mamba/envs/testbed/lib/python3.10/site-packages/neurokit2/__init__.py | heartpy installed: False origin: None | biopsykit version: 0.9.0 | biopsykit path: ['/root/.local/share/mamba/envs/testbed/lib/python3.10/site-packages/biopsykit'] | candidate modules: ['biopsykit.protocols.cft', 'biopsykit.protocol


===== POINT 11/38: t37s5@1791612745-277512 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t37 step 5] (333 chars)
# inspect_cft_formulas.py
import inspect
from biopsykit.protocols.cft import CFT

for method in ["baseline_hr", "extract_cft_interval", "onset", "peak_bradycardia", "mean_bradycardia", "poly_fit"]:
    print("\n" + "="*100)
    print(method, inspect.signature(getattr(CFT, method)))
    print(inspect.getsource(getattr(CFT, method)))
[OBS t37 step 5 first 500 chars]
exit_code: 0 | --- STDOUT --- |  | ==================================================================================================== | baseline_hr (self, data: pandas.core.frame.DataFrame) -> float |     def baseline_hr(self, data: pd.DataFrame) -> float: |         """Compute mean heart rate during Baseline Interval. |  |         The Baseline Interval is data in the interval [``0``, ``cft_start``]. |  |         .. warning:: |             If ``cft_start`` is 0, it is assumed that no Baseline is present and the firs


===== POINT 12/38: t37s8@1791614063-319742 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t37 step 8] (101 chars)
import inspect
from biopsykit.protocols.cft import CFT

src = inspect.getsource(CFT.onset)
print(src)
[OBS t37 step 8 first 500 chars]
exit_code: 0 | --- STDOUT --- |     def onset( |         self, |         data: pd.DataFrame, |         is_cft_interval: Optional[bool] = False, |         compute_baseline: Optional[bool] = True, |         hr_baseline: Optional[float] = None, |     ) -> Dict[str, Any]: |         """Compute **CFT onset**. |  |         The CFT onset is defined as the time point after beginning of the CFT Interval where three consecutive |         heart beats are lower than the Baseline heart rate (typically the Interval directly before th


===== POINT 13/38: t37s10@1791614063-319742 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t37 step 10] (2287 chars)
from pathlib import Path
import json

import pandas as pd
from biopsykit.protocols import CFT

# Load heart-rate data from the required sheet.
xlsx_path = Path("mist_hr/hr_sample_mist.xlsx")
sheet_name = "MIST3"
df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

print("Loaded:", xlsx_path, "sheet:", sheet_name)
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("First rows:")
print(df.head().to_string(index=False))
print("Last rows:")
print(df.tail().to_string(index=False))

# Prepare the dataframe expected by BioPsyKit's CFT implementation:
# a DatetimeIndex and a single heart-rate column.
hr = df.copy()
hr["time"] = pd.to_datetime(hr["time"])
hr = hr.set_index("time")[["Heart_Rate"]].sort_index()
hr = hr.dropna()

print("\nPrepared HR data:")
print("Shape:", hr.shape)
print("Index type:", type(hr.index).__name__)
print("Start:", hr.index[0], "End:", hr.index[-1])
print("Duration seconds:", (hr.index[-1] - hr.index[0]).total_seconds())
print(
    "HR min/mean/max:",
    float(hr["Heart_Rate"].min()),
    float(hr["Heart_Rate"].mean()),
    float(hr["Heart_Rate"].max()),
)

# Compute CFT parameters using the standard CFT structure:
# 60 s Baseline, 120 s CFT exposure, 60 s Recovery.
cft = CFT()
params_all = cft.compute_cft_parameter(hr, return_dict=True)

print("\nAll computed CFT parameters:")
for key, value in params_all.items():
    print(f"{key}: {value} ({type(value).__name__})")

# Extract required parameters and convert numpy/pandas scalar types to JSON-native floats.
required_keys = ["baseline_hr", "onset_hr", "onset_hr_percent"]
results = {}
missing_keys = []
for key in required_keys:
    if key not in params_all:
        missing_keys.append(key)
    else:
        value = params_all[key]
        if hasattr(value, "item"):
            value = value.item()
        results[key] = float(value)

if missing_keys:
    raise KeyError(f"Missing required computed keys: {missing_keys}")

# Save to the exact required output path.
out_path = Path("pred_results/cft_pred_results.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, sort_keys=True)

print("\nSaved required results to:", out_path)
print(json.dumps(results, indent=2, sort_keys=True))
[OBS t37 step 10 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded: mist_hr/hr_sample_mist.xlsx sheet: MIST3 | Shape: (350, 2) | Columns: ['time', 'Heart_Rate'] | First rows: |                    time  Heart_Rate | 2019-10-22 11:56:57.961  103.783784 | 2019-10-22 11:56:58.539   98.461538 | 2019-10-22 11:56:59.148   97.834395 | 2019-10-22 11:56:59.762  101.721854 | 2019-10-22 11:57:00.352  108.169014 | Last rows: |                    time  Heart_Rate | 2019-10-22 12:00:34.437  114.626866 | 2019-10-22 12:00:34.961  114.626866 | 2019-10-22 12:00:35.484  116


===== POINT 14/38: t40s2@1791613483-305791 =====
[TASK-DESC] Feature Engineering, Machine Learning
[STEP-CODE t40 step 2] (2264 chars)
#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

desc_path = "dili_MD/mol_descriptors_training.csv"
meta_path = "dili_MD/standardized_compounds_excl_ambiguous_cluster.csv"
test_path = "dili_MD/test.csv"

desc = pd.read_csv(desc_path)
meta = pd.read_csv(meta_path)
test = pd.read_csv(test_path)

print("Shapes:")
print("desc", desc.shape)
print("meta", meta.shape)
print("test", test.shape)

print("\nMETA columns:")
for i, c in enumerate(meta.columns):
    print(i, repr(c), str(meta[c].dtype), "nunique", meta[c].nunique(dropna=False))

print("\nTEST columns:")
for i, c in enumerate(test.columns):
    print(i, repr(c), str(test[c].dtype), "nunique", test[c].nunique(dropna=False))

print("\nMETA head selected:")
print(meta.head(10).to_string())

print("\nTEST head:")
print(test.head(10).to_string())

print("\nMeta value counts for likely label/split columns:")
for c in meta.columns:
    lc = c.lower()
    if any(k in lc for k in ["dili", "label", "split", "set", "train", "test", "concern", "cluster"]):
        print("\n", c)
        print(meta[c].value_counts(dropna=False).head(50).to_string())

print("\nTest value counts for likely columns:")
for c in test.columns:
    lc = c.lower()
    if any(k in lc for k in ["dili", "label", "split", "set", "train", "test", "concern", "cluster"]):
        print("\n", c)
        print(test[c].value_counts(dropna=False).head(50).to_string())

print("\nDescriptor index/first rows:")
print(desc.iloc[:10, :5].to_string())
print("desc first col min max unique?", desc.iloc[:,0].min(), desc.iloc[:,0].max(), desc.iloc[:,0].nunique())

# Check alignment: descriptor rows vs meta rows
print("\nAlignment checks:")
print("same n desc/meta?", len(desc)==len(meta))
if len(desc)==len(meta):
    print(pd.concat([desc.iloc[:5, [0]], meta.iloc[:5, :6]], axis=1).to_string())

# Non-finite counts in descriptors
X = desc.drop(columns=[desc.columns[0]])
arr = X.to_numpy(dtype=float)
print("\nDescriptor nonfinite:", np.size(arr) - np.isfinite(arr).sum(), "NaN:", np.isnan(arr).sum(), "inf:", np.isinf(arr).sum())
print("Columns with any NaN:", X.columns[X.isna().any()].tolist()[:20], "count", int(X.isna().any().sum()))
[OBS t40 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- | Shapes: | desc (923, 1176) | meta (923, 6) | test (55, 1176) |  | META columns: | 0 'Unnamed: 0' int64 nunique 923 | 1 'PubChem_CID' int64 nunique 923 | 2 'Compound Name' object nunique 903 | 3 'standardised_smiles' object nunique 904 | 4 'vDILIConcern' object nunique 4 | 5 'cluster' int64 nunique 632 |  | TEST columns: | 0 'Unnamed: 0' int64 nunique 55 | 1 'ABC' float64 nunique 55 | 2 'ABCGG' float64 nunique 55 | 3 'nAcid' float64 nunique 3 | 4 'nBase' float64 nunique 4 | 5 'SpAbs_A' float64 nunique 55 | 6


===== POINT 15/38: t40s2@1791614542-345089 =====
[TASK-DESC] Feature Engineering, Machine Learning
[STEP-CODE t40 step 2] (6685 chars)
#!/usr/bin/env python3
import os
import time
import json
import warnings
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from sklearn.metrics import balanced_accuracy_score, accuracy_score, f1_score, make_scorer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

np.random.seed(42)

BASE = "dili_MD"
OUTDIR = "pred_results"
os.makedirs(OUTDIR, exist_ok=True)

desc_path = os.path.join(BASE, "mol_descriptors_training.csv")
meta_path = os.path.join(BASE, "standardized_compounds_excl_ambiguous_cluster.csv")
test_path = os.path.join(BASE, "test.csv")

desc = pd.read_csv(desc_path)
meta = pd.read_csv(meta_path)
test = pd.read_csv(test_path)

print("Loaded:")
print("  training descriptors:", desc.shape)
print("  metadata:", meta.shape)
print("  test descriptors:", test.shape)

# Drop CSV index columns; keep a clean copy of test for output with original columns.
index_like = [c for c in desc.columns if str(c).startswith("Unnamed")]
feature_cols = [c for c in desc.columns if c not in index_like]
print("Index-like columns dropped from model:", index_like)
print("Feature count:", len(feature_cols))
print("Train/test feature columns equal:", feature_cols == [c for c in test.columns if c not in [x for x in test.columns if str(x).startswith('Unnamed')]])

X_all = desc[feature_cols].replace([np.inf, -np.inf], np.nan)
X_test = test[feature_cols].replace([np.inf, -np.inf], np.nan)

# Ensure alignment of descriptor rows and metadata rows.
if len(desc) != len(meta):
    raise ValueError(f"Descriptor rows ({len(desc)}) != metadata rows ({len(meta)})")
if "vDILIConcern" not in meta.columns:
    raise ValueError("Metadata file does not contain vDILIConcern")

print("\nClass counts in metadata:")
print(meta["vDILIConcern"].value_counts().to_string())

# Split definitions inferred from benchmark names:
# MCNC: Most-DILI-Concern vs No-DILI-Concern.
# MCLCNC: Most/Less-DILI-Concern vs No-DILI-Concern.
# all: Most/Less-DILI-Concern vs No-DILI-Concern/sider_inactive.
split_defs = {
    "MCNC": {
        "DILI": ["vMost-DILI-Concern"],
        "NoDILI": ["vNo-DILI-Concern"],
    },
    "MCLCNC": {
        "DILI": ["vMost-DILI-Concern", "vLess-DILI-Concern"],
        "NoDILI": ["vNo-DILI-Concern"],
    },
    "all": {
        "DILI": ["vMost-DILI-Concern", "vLess-DILI-Concer
[OBS t40 step 2 first 500 chars]
exit_code: None | --- STDOUT --- |  | --- STDERR --- |  | [TIMEOUT after 300.0s]


===== POINT 16/38: t40s4@1791613483-305791 =====
[TASK-DESC] Feature Engineering, Machine Learning
[STEP-CODE t40 step 4] (5926 chars)
#!/usr/bin/env python3
import os
import json
import time
import warnings
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, make_scorer
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

def log(*args):
    print(*args, flush=True)

def json_safe(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, dict):
        return {k: json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [json_safe(v) for v in x]
    return x

t0 = time.time()
RANDOM_STATE = 20251010
os.makedirs("pred_results", exist_ok=True)

log("Loading data...")
desc = pd.read_csv("dili_MD/mol_descriptors_training.csv")
meta = pd.read_csv("dili_MD/standardized_compounds_excl_ambiguous_cluster.csv")
test = pd.read_csv("dili_MD/test.csv")
log("Shapes:", {"desc": desc.shape, "meta": meta.shape, "test": test.shape})
log("vDILIConcern counts:\n" + meta["vDILIConcern"].value_counts().to_string())

id_col = desc.columns[0]
feature_cols = [c for c in desc.columns if c != id_col]
X_all = desc[feature_cols].replace([np.inf, -np.inf], np.nan)
X_test = test[feature_cols].replace([np.inf, -np.inf], np.nan)

all_nan = X_all.columns[X_all.isna().all()].tolist()
if all_nan:
    log("Dropping all-NaN columns:", len(all_nan))
    X_all = X_all.drop(columns=all_nan)
    X_test = X_test.drop(columns=all_nan)

# Pre-impute once for quick constant-column reporting; final imputation remains in pipeline.
constant_count = int((X_all.nunique(dropna=False) <= 1).sum())
log("Features:", X_all.shape[1], "constant-like columns:", constant_count,
    "NaNs train/test:", int(X_all.isna().sum().sum()), int(X_test.isna().sum().sum()))

split_defs = {
    "MCNC": {
        "positive": {"vMost-DILI-Concern"},
        "include": {"vMost-DILI-Concern", "vNo-DILI-Concern"},
    },
    "MCLCNC": {
        "positive": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "include": {"vMost-DILI-Concern", "vLess-DILI-Concern", "vNo-DILI-Concern"},
    },
    "all": {
        "positive": {"vMost-DILI-Concern", "vLess-DILI-Concern"},
        "include": None,
    },
}

# Compact but genuine hyperparameter search to stay within runtime.
param_distributions = {
    "rf__n_estimators": [120, 180, 240],
    "rf__max_dept
[OBS t40 step 4 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loading data... | Shapes: {'desc': (923, 1176), 'meta': (923, 6), 'test': (55, 1176)} | vDILIConcern counts: | vDILIConcern | sider_inactive        262 | vLess-DILI-Concern    260 | vNo-DILI-Concern      227 | vMost-DILI-Concern    174 | Features: 1175 constant-like columns: 138 NaNs train/test: 0 0 |  | === Training split: MCNC === | Rows/features: (401, 1175) | Raw labels: | vDILIConcern | vNo-DILI-Concern      227 | vMost-DILI-Concern    174 | Binary counts: {'DILI': 174, 'NoDILI': 227} | Best sear


===== POINT 17/38: t44s4@1791613127-299358 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t44 step 4] (2668 chars)
#!/usr/bin/env python3
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration

Path("pred_results").mkdir(exist_ok=True)

df = pd.read_pickle("sleep_imu_data/sleep_data.pkl")
acc = df[["acc_x", "acc_y", "acc_z"]]
dt = pd.Series(df.index).diff().dt.total_seconds().median()
sampling_rate = 1.0 / dt
print("Loaded acceleration:", acc.shape)
print("Index start/end:", acc.index[0], acc.index[-1])
print("Median dt:", dt, "sampling_rate:", sampling_rate)

t0 = time.time()
try:
    result = predict_pipeline_acceleration(
        acc,
        sampling_rate=sampling_rate,
        convert_to_g=True,
        algorithm_type="cole_kripke",
        epoch_length=60,
    )
    print("Pipeline completed in seconds:", time.time() - t0)
    print("Result type:", type(result), "keys:", list(result.keys()) if isinstance(result, dict) else None)
    if isinstance(result, dict):
        for k, v in result.items():
            print("\nKEY:", k, "TYPE:", type(v))
            if isinstance(v, pd.DataFrame):
                print("shape:", v.shape)
                print(v.head().to_string())
                print(v.tail().to_string())
            else:
                print(repr(v)[:2000])
        endpoints = result.get("sleep_endpoints", {})
        print("\nSleep endpoints:")
        print(repr(endpoints))
        # Save raw endpoint repr for inspection
        Path("pred_results/pipeline_endpoints_repr.txt").write_text(repr(endpoints))
        # If possible, save requested JSON now
        def jsonable(x):
            if isinstance(x, (pd.Timestamp, np.datetime64)):
                return str(pd.Timestamp(x))
            if isinstance(x, pd.Timedelta):
                return str(x)
            if isinstance(x, np.timedelta64):
                return str(pd.Timedelta(x))
            if isinstance(x, (np.integer,)):
                return int(x)
            if isinstance(x, (np.floating,)):
                return float(x)
            return x
        if endpoints:
            pred = {
                "sleep_onset": jsonable(endpoints.get("sleep_onset")),
                "wake_onset": jsonable(endpoints.get("wake_onset")),
                "total_sleep_duration": jsonable(endpoints.get("total_sleep_duration")),
            }
            Path("pred_results/imu_pred.json").write_text(json.dumps(pred, indent=2))
            print("Wrote pred_results/imu_pred.json:")
            print(json.dumps(pred, indent=2))
except Exception as e:
    print("Pipeline failed:", type(
[OBS t44 step 4 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded acceleration: (4048332, 3) | Index start/end: 2019-09-03 02:06:18.251953+02:00 2019-09-03 07:35:45.493164+02:00 | Median dt: 0.004883 sampling_rate: 204.79213598197828 | Pipeline completed in seconds: 14.839076280593872 | Result type: <class 'dict'> keys: ['wear_detection', 'activity_counts', 'sleep_wake_prediction', 'major_wear_block', 'rest_periods', 'bed_interval', 'sleep_endpoints'] |  | KEY: wear_detection TYPE: <class 'pandas.core.frame.DataFrame'> | shape: (19, 3) |    


===== POINT 18/38: t44s4@1791614343-341588 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t44 step 4] (653 chars)
#!/usr/bin/env python3
import inspect
from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration
from biopsykit.sleep.sleep_endpoints import compute_sleep_endpoints
import biopsykit.sleep.sleep_processing_pipeline.sleep_processing_pipeline as spp

src = inspect.getsource(spp)
lines = src.splitlines()
print("sleep_processing_pipeline source line count:", len(lines))
for i, line in enumerate(lines[:260], start=1):
    print(f"{i:03d}: {line}")

print("\ncompute_sleep_endpoints full source:")
src2 = inspect.getsource(compute_sleep_endpoints)
for i, line in enumerate(src2.splitlines(), start=1):
    print(f"{i:03d}: {line}")
[OBS t44 step 4 first 500 chars]
exit_code: 0 | --- STDOUT --- | sleep_processing_pipeline source line count: 135 | 001: """Functions to process sleep data from raw IMU data or Actigraph data.""" | 002: from typing import Any, Dict, Optional, Sequence, Union | 003:  | 004: import numpy as np | 005: from biopsykit.signals.imu import convert_acc_data_to_g | 006: from biopsykit.signals.imu.activity_counts import ActivityCounts | 007: from biopsykit.signals.imu.rest_periods import RestPeriods | 008: from biopsykit.signals.imu.wear_detection import Wea


===== POINT 19/38: t44s5@1791613127-299358 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t44 step 5] (1097 chars)
#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import pandas as pd
from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration

out_path = Path("pred_results/imu_pred.json")
out_path.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_pickle("sleep_imu_data/sleep_data.pkl")
acc = df[["acc_x", "acc_y", "acc_z"]]
sampling_rate = 1.0 / pd.Series(df.index).diff().dt.total_seconds().median()

print("Running/confirming BioPsyKit acceleration sleep pipeline")
print("Samples:", len(acc), "sampling_rate:", sampling_rate)
print("Recording:", df.index[0], "to", df.index[-1])

result = predict_pipeline_acceleration(
    acc,
    sampling_rate=sampling_rate,
    convert_to_g=True,
    algorithm_type="cole_kripke",
    epoch_length=60,
)
endpoints = result["sleep_endpoints"]
pred = {
    "sleep_onset": endpoints["sleep_onset"],
    "wake_onset": endpoints["wake_onset"],
    "total_sleep_duration": endpoints["total_sleep_duration"],
}

out_path.write_text(json.dumps(pred, indent=2))
print("Saved:", out_path)
print(out_path.read_text())
[OBS t44 step 5 first 500 chars]
exit_code: 0 | --- STDOUT --- | Running/confirming BioPsyKit acceleration sleep pipeline | Samples: 4048332 sampling_rate: 204.79213598197828 | Recording: 2019-09-03 02:06:18.251953+02:00 to 2019-09-03 07:35:45.493164+02:00 | Saved: pred_results/imu_pred.json | { |   "sleep_onset": "2019-09-03 02:07:18+02:00", |   "wake_onset": "2019-09-03 07:00:18+02:00", |   "total_sleep_duration": 311 | } |  | --- STDERR --- | Matplotlib created a temporary cache directory at /var/tmp/matplotlib-7ydd00c6 because the default path (/roo


===== POINT 20/38: t45s1@1791613957-319021 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t45 step 1] (2482 chars)
#!/usr/bin/env python3
import os
import pickle
from pathlib import Path

import pandas as pd

DATA_PATH = Path("biopsykit_questionnaire_data/questionnaire_data.pkl")
OUT_PATH = Path("pred_results/questionnaire_pred.csv")

def load_dataframe(path: Path) -> pd.DataFrame:
    obj = pd.read_pickle(path)
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    # fallback in case pickle contains another object convertible to DataFrame
    return pd.DataFrame(obj)

def main():
    df = load_dataframe(DATA_PATH)
    print("Loaded:", DATA_PATH)
    print("Shape:", df.shape)
    print("Columns first 15:", list(df.columns[:15]))
    print("Index name:", df.index.name)

    # Ensure subject is available as a column.
    if "subject" not in df.columns:
        if df.index.name == "subject" or df.index.dtype == object:
            df = df.reset_index()
            if "index" in df.columns and "subject" not in df.columns:
                df = df.rename(columns={"index": "subject"})
        else:
            raise ValueError("Could not find subject column or suitable subject index.")

    pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
    missing = [c for c in pss_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing PSS columns: {missing}")

    pss = df[pss_cols].apply(pd.to_numeric)

    # PSS-10 scoring:
    # Negatively phrased/helplessness items: 1,2,3,6,9,10 scored directly.
    # Positively phrased/self-efficacy items: 4,5,7,8 reverse scored on 0..4 as 4 - response.
    helpless_cols = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
    selfeff_cols = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

    perceived_helplessness = pss[helpless_cols].sum(axis=1)
    perceived_self_efficacy = (4 - pss[selfeff_cols]).sum(axis=1)
    total_pss = perceived_helplessness + perceived_self_efficacy

    out = pd.DataFrame({
        "subject": df["subject"],
        "perceived_helplessness": perceived_helplessness.astype(int),
        "perceived_self_efficacy": perceived_self_efficacy.astype(int),
        "total_pss": total_pss.astype(int),
    })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False, header=False)

    print("PSS response min/max:", int(pss.min().min()), int(pss.max().max()))
    print("Output shape:", out.shape)
    print("First 5 output rows:")
    print(out.head().to_string(index=False))
    print("Saved:", OUT_PATH)

if __name__ == "__main__":
    main()
[OBS t45 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded: biopsykit_questionnaire_data/questionnaire_data.pkl | Shape: (13, 66) | Columns first 15: ['PSS_01', 'PSS_02', 'PSS_03', 'PSS_04', 'PSS_05', 'PSS_06', 'PSS_07', 'PSS_08', 'PSS_09', 'PSS_10', 'PANAS_01_Pre', 'PANAS_02_Pre', 'PANAS_03_Pre', 'PANAS_04_Pre', 'PANAS_05_Pre'] | Index name: subject | PSS response min/max: 0 4 | Output shape: (13, 4) | First 5 output rows: | subject  perceived_helplessness  perceived_self_efficacy  total_pss |    Vp01                      14         


===== POINT 21/38: t5s1@1791614495-343084 =====
[TASK-DESC] Use the DKPES dataset to develop a Random Forest classifier predicting signal inhibition of chemicals while choosing appropriate threshold to assign binary labels based on signal inhibition values. Save the test set predictions, including the index and predicted signal inhibition, in "pred_results/dkpes_test_pred.csv".
[STEP-CODE t5 step 1] (8668 chars)
#!/usr/bin/env python3
import os
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score, average_precision_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


RANDOM_STATE = 42
TRAIN_PATH = "dkpes/dkpes_train.csv"
TEST_PATH = "dkpes/dkpes_test.csv"
OUT_DIR = "pred_results"
OUT_PATH = os.path.join(OUT_DIR, "dkpes_test_pred.csv")


def otsu_threshold(values, bins=256):
    """Otsu threshold for a 1D continuous target."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return float(np.nanmedian(values))
    counts, edges = np.histogram(values, bins=min(bins, max(2, len(np.unique(values)))))
    centers = (edges[:-1] + edges[1:]) / 2.0
    total = counts.sum()
    if total == 0:
        return float(np.nanmedian(values))

    weight1 = np.cumsum(counts)
    weight2 = total - weight1
    mean1_num = np.cumsum(counts * centers)
    mean_total = mean1_num[-1]
    valid = (weight1 > 0) & (weight2 > 0)

    mean1 = np.zeros_like(centers)
    mean2 = np.zeros_like(centers)
    mean1[valid] = mean1_num[valid] / weight1[valid]
    mean2[valid] = (mean_total - mean1_num[valid]) / weight2[valid]

    between = weight1 * weight2 * (mean1 - mean2) ** 2
    between[~valid] = -np.inf
    return float(centers[int(np.argmax(between))])


def make_ohe():
    # compatibility with older/newer sklearn
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_pipeline(feature_df):
    categorical_cols = feature_df.select_dtypes(include=["object", "category"]).columns.tolist()
    numeric_cols = [c for c in feature_df.columns if c not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_cols),
            ("cat", make_ohe(), categorical_cols),
        ],
        remainder="drop",
    )

    clf = RandomForestClassifier(
        n_estimators=700,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    return Pipeline([("preprocess", preprocessor), ("rf", clf)]), numeric_cols, ca
[OBS t5 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loading data... | Train shape: (44, 27) | Test shape:  (12, 27) | Train columns: ['index', 'Signal-inhibition', '3-Keto', '3-Hydroxy', '12-Keto', '12-Hydroxy', '19-Methyl', '18-Methyl', 'Sulfate-Ester', 'Sulfate-Oxygens', 'C4-C5-DB', 'C6-C7-DB', 'Sulfur', 'ShapeQuery', 'TanimotoCombo', 'ShapeTanimoto', 'ColorTanimoto', 'FitTverskyCombo', 'FitTversky', 'FitColorTversky', 'RefTverskyCombo', 'RefTversky', 'RefColorTversky', 'ScaledColor', 'ComboScore', 'ColorScore', 'Overlap']


===== POINT 22/38: t5s2@1791613243-300389 =====
[TASK-DESC] Use the DKPES dataset to develop a Random Forest classifier predicting signal inhibition of chemicals while choosing appropriate threshold to assign binary labels based on signal inhibition values. Save the test set predictions, including the index and predicted signal inhibition, in "pred_results/dkpes_test_pred.csv".
[STEP-CODE t5 step 2] (6374 chars)
#!/usr/bin/env python3
import os
import json
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, accuracy_score, f1_score, roc_auc_score, mean_absolute_error
from sklearn.model_selection import StratifiedKFold, LeaveOneOut, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

RANDOM_STATE = 42

train = pd.read_csv("dkpes/dkpes_train.csv")
test = pd.read_csv("dkpes/dkpes_test.csv")

print("Train shape:", train.shape, "Test shape:", test.shape)
print("Signal-inhibition sorted:")
print(np.array2string(np.sort(train["Signal-inhibition"].values), precision=3, separator=", "))

feature_cols = [c for c in train.columns if c not in ["index", "Signal-inhibition"]]
X = train[feature_cols]
y_cont = train["Signal-inhibition"].astype(float).values

cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
num_cols = [c for c in feature_cols if c not in cat_cols]
print("Categorical columns:", cat_cols)
print("Numeric columns:", len(num_cols), num_cols)

# Compatible OneHotEncoder argument across sklearn versions
try:
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
except TypeError:
    ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)

preprocess = ColumnTransformer(
    transformers=[
        ("num", SimpleImputer(strategy="median"), num_cols),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("ohe", ohe)]), cat_cols),
    ],
    remainder="drop",
)

def make_clf():
    return Pipeline([
        ("prep", preprocess),
        ("rf", RandomForestClassifier(
            n_estimators=1000,
            random_state=RANDOM_STATE,
            class_weight="balanced",
            min_samples_leaf=1,
            max_features="sqrt",
            n_jobs=-1,
        )),
    ])

# Evaluate plausible thresholds. Need both classes with enough members for stratified CV.
candidate_thresholds = sorted(set(
    [0.40, 0.45, 0.50, 0.55, 0.60, float(np.median(y_cont))] +
    [float(q) for q in np.quantile(y_cont, [0.25, 0.33, 0.5, 0.67, 0.75])]
))
rows = []
for thr in candidate_thresholds:
    y_bin = (y_cont >= thr).astype(int)
    n_pos = int(y_bin.sum())
    n_neg = int(len(y_bin) - n_pos)
    if n_pos < 3 or n_neg < 3:
        continue
    n_splits = min(5, n_pos, n_neg)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    
[OBS t5 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- | Train shape: (44, 27) Test shape: (12, 27) | Signal-inhibition sorted: | [0.   , 0.032, 0.033, 0.044, 0.108, 0.136, 0.158, 0.17 , 0.174, 0.183, |  0.186, 0.186, 0.195, 0.209, 0.213, 0.226, 0.237, 0.24 , 0.263, 0.269, |  0.278, 0.28 , 0.288, 0.297, 0.318, 0.334, 0.354, 0.365, 0.399, 0.414, |  0.483, 0.484, 0.484, 0.488, 0.515, 0.623, 0.624, 0.627, 0.686, 0.722, |  0.739, 0.845, 0.897, 0.904] | Categorical columns: ['ShapeQuery'] | Numeric columns: 24 ['3-Keto', '3-Hydroxy', '12-Keto',


===== POINT 23/38: t53s1@1791612802-278586 =====
[TASK-DESC] Standardize land cover and protected status datasets for consistency in analysis for mountain lion habitat. Reclassify these categorical datasets to a common scale using geospatial tools. Save the reclassified data as pred_results/landCover_reclassified.tif and pred_results/protected_status_reclassified.tif.
[STEP-CODE t53 step 1] (5669 chars)
#!/usr/bin/env python3
"""
Reclassify land cover and protected status rasters to a common 1-10 scale.

Outputs:
  pred_results/landCover_reclassified.tif
  pred_results/protected_status_reclassified.tif
"""

from pathlib import Path
import sys
import numpy as np

try:
    import rasterio
except Exception as e:
    print("ERROR: rasterio is required but could not be imported:", repr(e))
    sys.exit(1)


DATA_DIR = Path("MountainLionNew")
OUT_DIR = Path("pred_results")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAND_SRC = DATA_DIR / "landCover.tif"
PROT_SRC = DATA_DIR / "Protected_Status.tif"

LAND_OUT = OUT_DIR / "landCover_reclassified.tif"
PROT_OUT = OUT_DIR / "protected_status_reclassified.tif"

landCover_classification = {
    11: 10,  # Open Water
    21: 8,   # Developed, Open Space
    22: 7,   # Developed, Low Intensity
    23: 8,   # Developed, Medium Intensity
    24: 9,   # Developed, High Intensity
    31: 6,   # Barren Land
    41: 2,   # Deciduous Forest
    42: 1,   # Evergreen Forest
    43: 2,   # Mixed Forest
    52: 3,   # Shrub/Scrub
    71: 3,   # Grassland/Herbaceous
    72: 3,   # Sedge/Herbaceous
    81: 4,   # Hay/Pasture
    82: 6,   # Cultivated Crops
    90: 4,   # Woody Wetlands
    95: 4,   # Emergent Herbaceous Wetlands
    255: 10
}

protected_status_classification = {
    0: 1,
    1: 3,
    2: 6,
    3: 9,
    4: 10,
    255: 10
}


def bincount_raster_values(path):
    """Return dict of value counts for a single-band integer raster."""
    counts = {}
    with rasterio.open(path) as src:
        for _, window in src.block_windows(1):
            arr = src.read(1, window=window, masked=False)
            vals, cnts = np.unique(arr, return_counts=True)
            for v, c in zip(vals.tolist(), cnts.tolist()):
                counts[int(v)] = counts.get(int(v), 0) + int(c)
    return dict(sorted(counts.items()))


def reclassify_raster(src_path, out_path, mapping, default_value=0):
    """
    Reclassify a uint/integer categorical raster using an explicit value mapping.
    Unmapped values are written as default_value, used here as NoData/unknown.
    """
    if not src_path.exists():
        raise FileNotFoundError(f"Missing source raster: {src_path}")

    # Make a lookup table for the common uint8 categorical rasters.
    lut = np.full(256, default_value, dtype=np.uint8)
    for old, new in mapping.items():
        if not (0 <= int(old) <= 255):
            raise ValueError(f"Mapping key outside uint8 range: {old}")
        if not (0 <= int(new) <= 255):
            raise ValueError(f"Mapping value outside uint8 range
[OBS t53 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Starting raster reclassification for mountain lion habitat predictors. | Working directory outputs will be saved in: /tmp/vf_work/sab_53/frontier/73a13490582a/wd/pred_results |  | Source: MountainLionNew/landCover.tif |   size: 3062 x 2494; dtype=uint8; crs=EPSG:26911 |   transform: | 30.00, 0.00, 307049.44| | | 0.00,-30.00, 3837890.35| | | 0.00, 0.00, 1.00| |   source nodata: None |   source unique counts: {0: 160768, 11: 34171, 21: 700756, 22: 641523, 23: 747095, 24: 176973, 31: 3434


===== POINT 24/38: t58s2@1791612832-278797 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t58 step 2] (1503 chars)
#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import csv
import os

def show_file(path, max_chars=5000):
    print(f"\n===== RAW {path} =====")
    p = Path(path)
    if not p.exists():
        print("MISSING")
        return
    txt = p.read_text(errors="replace")
    print(txt[:max_chars])
    print(f"--- length {len(txt)} chars ---")

show_file("nvc/ind_data_for_plot.csv", 10000)
show_file("nvc/accuracies_data_for_plot.csv", 3000)
show_file("nvc/valid_syllogisms.csv", 3000)

# More compact CSV inspection for models
for path in sorted(Path("nvc/scripts/indiv_table/models").glob("*.csv")):
    print(f"\n===== RAW MODEL {path.name} =====")
    print(path.read_text()[:2000])

# Inspect full rule files compactly
for path in sorted(Path("nvc/scripts/indiv_table/rules").glob("*.py")):
    print(f"\n===== RULE {path.name} =====")
    print(path.read_text())

# Analyze Ragni dimensions, individuals counts and responses
df = pd.read_csv("nvc/Ragni2016.csv")
print("\n===== Ragni summary =====")
print("shape", df.shape)
print("n ids", df["id"].nunique(), "min rows per id", df.groupby("id").size().min(), "max", df.groupby("id").size().max())
print("task count", df["task"].nunique())
print("sequence range", df["sequence"].min(), df["sequence"].max())
print("response counts top")
print(df["response"].value_counts().head(20).to_string())
print("first id tasks/responses")
print(df[df.id == df.id.min()].head(64)[["id","sequence","task","response"]].to_string(index=False))
[OBS t58 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- |  | ===== RAW nvc/ind_data_for_plot.csv ===== | Model;Rule;Num persons | PSYCOP;PartNeg;41 | PSYCOP;EmptyStart;43 | PSYCOP;FiguralRule;24 | PSYCOP;NegativityRule;49 | PSYCOP;ParticularityRule;49 | Matching;PartNeg;70 | Matching;EmptyStart;18 | Matching;FiguralRule;12 | Matching;NegativityRule;32 | Matching;ParticularityRule;17 | VerbalModels;PartNeg;56 | VerbalModels;EmptyStart;22 | VerbalModels;FiguralRule;16 | VerbalModels;NegativityRule;34 | VerbalModels;ParticularityRule;16 | MMT;PartNeg;63 | MMT;Empty


===== POINT 25/38: t58s2@1791614139-321155 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t58 step 2] (1490 chars)
import os
from pathlib import Path
import pandas as pd

# Print a more focused inspection to infer the intended computation.
paths = [
    Path("nvc/ind_data_for_plot.csv"),
    Path("nvc/accuracies_data_for_plot.csv"),
    Path("nvc/valid_syllogisms.csv"),
]
for p in paths:
    print("\n==", p, "==")
    df = pd.read_csv(p)
    print("shape", df.shape)
    print("columns", list(df.columns))
    print(df.head(20).to_string(index=False))
    print("dtypes", df.dtypes.to_dict())

# Locate any scripts/notebooks that may have generated indiv_table.png or expected individuals.csv.
print("\nPython/script files under nvc:")
for p in sorted(Path("nvc").rglob("*")):
    if p.suffix.lower() in [".py", ".R", ".ipynb", ".sh"]:
        print(p)

# Inspect all Python files in nvc/scripts except rule modules.
for p in sorted(Path("nvc/scripts").rglob("*.py")):
    if "/rules/" in str(p).replace("\\", "/"):
        continue
    print("\n== PY", p, "==")
    txt = p.read_text(errors="replace")
    print("\n".join(txt.splitlines()[:250]))

# Show all model CSV contents fully (small files).
for d in [Path("nvc/scripts/indiv_table/models"), Path("nvc/scripts/prediction_errors/models")]:
    print("\nMODEL DIR", d)
    for p in sorted(d.glob("*.csv")):
        print("\n--", p.name, "--")
        print(p.read_text())

# Show rule files fully from indiv_table.
for p in sorted(Path("nvc/scripts/indiv_table/rules").glob("*.py")):
    print("\n== RULE", p.name, "==")
    print(p.read_text())
[OBS t58 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- |  | == nvc/ind_data_for_plot.csv == | shape (35, 1) | columns ['Model;Rule;Num persons'] |            Model;Rule;Num persons |                 PSYCOP;PartNeg;41 |              PSYCOP;EmptyStart;43 |             PSYCOP;FiguralRule;24 |          PSYCOP;NegativityRule;49 |       PSYCOP;ParticularityRule;49 |               Matching;PartNeg;70 |            Matching;EmptyStart;18 |           Matching;FiguralRule;12 |        Matching;NegativityRule;32 |     Matching;ParticularityRule;17 |           Verbal


===== POINT 26/38: t60s2@1791614180-321913 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t60 step 2] (904 chars)
#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
base=Path("nvc")

pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 200)

for rel in ["valid_syllogisms.csv","accuracies_data_for_plot.csv","ind_data_for_plot.csv"]:
    df=pd.read_csv(base/rel)
    print("\n==",rel,"==")
    print("shape",df.shape)
    print("columns",df.columns.tolist())
    print(df.head(20).to_string(index=False))
    print("tail")
    print(df.tail(10).to_string(index=False))

print("\n== all model csvs ==")
for path in sorted((base/"scripts/indiv_table/models").glob("*.csv")):
    df=pd.read_csv(path)
    print("\n",path.name, df.shape, df.columns.tolist())
    print(df.head(8).to_string(index=False))

print("\n== rule source snippets ==")
for path in sorted((base/"scripts/nvc_prediction/rules").glob("*.py")):
    print("\n---", path.name, "---")
    print(path.read_text()[:2500])
[OBS t60 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- |  | == valid_syllogisms.csv == | shape (64, 2) | columns ['syllog', 'is_valid'] | syllog  is_valid |    AA1      True |    AA2      True |    AA3     False |    AA4      True |    AI1     False |    AI2      True |    AI3     False |    AI4      True |    AE1      True |    AE2      True |    AE3      True |    AE4      True |    AO1     False |    AO2     False |    AO3      True |    AO4      True |    IA1      True |    IA2     False |    IA3     False |    IA4      True | tail | syllog  is_valid |    OI3     False |    


===== POINT 27/38: t60s3@1791612902-279436 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t60 step 3] (3210 chars)
#!/usr/bin/env python3
import os, glob
import pandas as pd

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 160)

# Inspect compact facts needed to decide/reproduce output.
acc = pd.read_csv("nvc/accuracies_data_for_plot.csv")
print("Existing accuracies_data_for_plot:", acc.shape, list(acc.columns))
print("Any missing values?\n", acc.isna().sum().to_string())
print("Duplicate key rows model/nvc/task:", acc.duplicated(["model","nvc","task"]).sum())
print("Rows not equal to full 7*5*64:", 7*5*64, "actual", len(acc))

missing = []
for m in sorted(acc.model.unique()):
    for r in sorted(acc.nvc.unique()):
        tasks = set(acc[(acc.model==m)&(acc.nvc==r)].task)
        if len(tasks) != 64:
            missing.append((m,r,64-len(tasks), sorted(set(acc.task.unique())-tasks)))
print("Incomplete model/rule task sets:", missing)

print("\nTruth count in existing file (unique per task):")
truth_by_task = acc.groupby("task")["truth"].nunique()
print("tasks with nonunique truth:", truth_by_task[truth_by_task != 1].to_dict())
truth = acc.drop_duplicates("task")[["task","truth"]].sort_values("task")
print(truth.head(20).to_string(index=False))
print("truth value counts:\n", truth["truth"].value_counts().to_string())

# Derive most frequent answers from participant data to compare.
rag = pd.read_csv("nvc/Ragni2016.csv")
print("\nRagni shape/cols:", rag.shape, list(rag.columns))
print("unique sequences:", rag.sequence.nunique(), "unique ids:", rag.id.nunique())

# Convert task text to syllogism code if possible.
quant_map = {"All":"A", "Some":"I", "Some not":"O", "No":"E"}
def premise_quant(p):
    return quant_map[p.split(";")[0]]
def figure_from_task(task):
    p1, p2 = task.split("/")
    _, s1, p1t = p1.split(";")
    _, s2, p2t = p2.split(";")
    # conclusion terms are the two non-middle terms. Determine figure by middle placement:
    # figures with premises encoded as: 1 M-P/S-M, 2 P-M/S-M, 3 M-P/M-S, 4 P-M/M-S (using a,b,c terms convention)
    terms = [s1,p1t,s2,p2t]
    # middle is repeated term
    middle = [x for x in set(terms) if terms.count(x)==2][0]
    pos1 = "subj" if s1 == middle else "pred"
    pos2 = "subj" if s2 == middle else "pred"
    return {("subj","pred"):1, ("pred","pred"):2, ("subj","subj"):3, ("pred","subj"):4}[(pos1,pos2)]
def task_code(task):
    p1, p2 = task.split("/")
    return premise_quant(p1) + premise_quant(p2) + str(figure_from_task(task))

rag["task_code"] = rag["task"].map(task_code)
print("task_code nunique:", rag.task_code.nunique())
mfa = rag.groupby("task_code")["response"].agg(lambda s: s.value
[OBS t60 step 3 first 500 chars]
exit_code: 0 | --- STDOUT --- | Existing accuracies_data_for_plot: (2235, 9) ['model', 'nvc', 'task', 'prediction', 'plain_prediction', 'truth', 'improvement', 'hit_model', 'hit_nvc'] | Any missing values? |  model               0 | nvc                 0 | task                0 | prediction          0 | plain_prediction    0 | truth               0 | improvement         0 | hit_model           0 | hit_nvc             0 | Duplicate key rows model/nvc/task: 0 | Rows not equal to full 7*5*64: 2240 actual 2235 | Incomplete model


===== POINT 28/38: t60s4@1791614180-321913 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t60 step 4] (1297 chars)
#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from collections import Counter
base=Path("nvc")
rag=pd.read_csv(base/"Ragni2016.csv")
print("Ragni shape",rag.shape)
print("unique sequences",rag.sequence.nunique(), "minmax",rag.sequence.min(), rag.sequence.max())
# Compute response frequencies per sequence/task
freq=(rag.groupby(["sequence","task","response"]).size().reset_index(name="n")
      .sort_values(["sequence","n","response"], ascending=[True,False,True]))
mfa=freq.groupby(["sequence","task"]).head(3)
print("\nTop responses per sequence first 20 groups:")
for seq in range(0,20):
    sub=mfa[mfa.sequence==seq]
    print("\nSEQ",seq)
    print(sub.to_string(index=False))

# Existing truths keyed task codes
acc=pd.read_csv(base/"accuracies_data_for_plot.csv")
truth=acc[["task","truth"]].drop_duplicates().sort_values("task")
print("\nExisting truth mapping:")
print(truth.to_string(index=False))

# Inspect ind_data_for_plot
ind=pd.read_csv(base/"ind_data_for_plot.csv")
print("\nind_data_for_plot:")
print(ind.to_string(index=False))

# model accuracy means in existing acc
print("\nExisting mean accuracies by model/rule:")
summary=acc.groupby(["model","nvc"])[["hit_model","hit_nvc","improvement"]].mean().reset_index()
print(summary.to_string(index=False))
[OBS t60 step 4 first 500 chars]
exit_code: 0 | --- STDOUT --- | Ragni shape (8896, 9) | unique sequences 64 minmax 0 63 |  | Top responses per sequence first 20 groups: |  | SEQ 0 |  sequence                                              task                     response  n |         0             All;managers;clerks/All;clerks;models          All;managers;models  3 |         0           All;typists;dancers/Some;boxers;typists          Some;boxers;dancers  2 |         0          All;packers;tutors/Some;butchers;packers         Some;butchers;tutors  


===== POINT 29/38: t60s6@1791612902-279436 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t60 step 6] (3082 chars)
#!/usr/bin/env python3
import os
import pandas as pd

pd.set_option("display.max_columns", 60)
pd.set_option("display.width", 220)
pd.set_option("display.max_rows", 120)

rag = pd.read_csv("nvc/Ragni2016.csv")

quant_map = {"All":"A", "Some":"I", "Some not":"O", "No":"E"}
rev_quant = {v:k for k,v in quant_map.items()}

def figure_from_task(task):
    p1, p2 = task.split("/")
    q1, s1, p1t = p1.split(";")
    q2, s2, p2t = p2.split(";")
    terms = [s1, p1t, s2, p2t]
    middle_terms = [x for x in set(terms) if terms.count(x) == 2]
    if len(middle_terms) != 1:
        raise ValueError(("bad middle", task, middle_terms))
    m = middle_terms[0]
    pos1 = "subj" if s1 == m else "pred"
    pos2 = "subj" if s2 == m else "pred"
    return {("subj","pred"):1, ("pred","pred"):2, ("subj","subj"):3, ("pred","subj"):4}[(pos1,pos2)]

def task_code(task):
    p1, p2 = task.split("/")
    return quant_map[p1.split(";")[0]] + quant_map[p2.split(";")[0]] + str(figure_from_task(task))

def conclusion_terms_from_choices(choices):
    opts = choices.split("|")
    non_nvc = [o for o in opts if o != "NVC"]
    first = non_nvc[0].split(";")
    return first[1], first[2]  # a,c orientation as presented by code's ac

def response_code(row):
    r = row["response"]
    if r == "NVC":
        return "NVC"
    parts = r.split(";")
    if len(parts) != 3 or parts[0] not in quant_map:
        return None
    q = quant_map[parts[0]]
    a, c = conclusion_terms_from_choices(row["choices"])
    if parts[1] == a and parts[2] == c:
        return q + "ac"
    if parts[1] == c and parts[2] == a:
        return q + "ca"
    return "OTHER"

rag["task_code"] = rag["task"].map(task_code)
rag["resp_code"] = rag.apply(response_code, axis=1)

print("Rows:", len(rag), "task_code nunique:", rag.task_code.nunique())
print("resp_code counts:")
print(rag["resp_code"].value_counts(dropna=False).to_string())

print("\nPer task response-code counts and MFA:")
rows = []
for task, sub in rag.groupby("task_code"):
    vc = sub["resp_code"].value_counts(dropna=False)
    # Exclude OTHER? First print both incl and choice-only.
    vc_choice = sub.loc[sub["resp_code"]!="OTHER", "resp_code"].value_counts()
    rows.append({
        "task": task,
        "n": len(sub),
        "OTHER": int(vc.get("OTHER", 0)),
        "mfa_incl_other": vc.index[0],
        "mfa_incl_other_n": int(vc.iloc[0]),
        "mfa_choice": vc_choice.index[0] if len(vc_choice) else None,
        "mfa_choice_n": int(vc_choice.iloc[0]) if len(vc_choice) else 0,
        "counts_choice": "; ".join(f"{k}:{v}" for k,v in vc_choice.items(
[OBS t60 step 6 first 500 chars]
exit_code: 0 | --- STDOUT --- | Rows: 8896 task_code nunique: 64 | resp_code counts: | resp_code | NVC    2468 | Oac    1191 | Iac    1170 | Oca    1169 | Ica     936 | Eac     805 | Eca     675 | Aac     288 | Aca     194 |  | Per task response-code counts and MFA: | task   n  OTHER mfa_incl_other  mfa_incl_other_n mfa_choice  mfa_choice_n                                                        counts_choice |  AA1 139      0            Aca                81        Aca            81             Aca:81; Aac:33; Iac:8; Ica:6; NVC:


===== POINT 30/38: t60s8@1791614180-321913 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t60 step 8] (5581 chars)
#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import pandas as pd

BASE = Path("nvc")
OUTDIR = Path("pred_results")
OUTFILE = OUTDIR / "accuracies.csv"

QUANT_TO_MOOD = {"All": "A", "Some": "I", "Some not": "O", "No": "E"}

def parse_statement(stmt: str):
    parts = stmt.split(";")
    if len(parts) != 3:
        raise ValueError(f"Cannot parse statement: {stmt!r}")
    return parts[0], parts[1], parts[2]

def response_code(resp: str, choices: str) -> str:
    """Convert a natural-language response to compact syllogistic code, e.g. Aac."""
    if resp == "NVC":
        return "NVC"
    q, subj, pred = parse_statement(resp)
    first_non_nvc = next(c for c in choices.split("|") if c != "NVC")
    _, a, c = parse_statement(first_non_nvc)
    if subj == a and pred == c:
        direction = "ac"
    elif subj == c and pred == a:
        direction = "ca"
    else:
        raise ValueError(f"Response terms not end terms: response={resp!r}, choices={choices!r}")
    return QUANT_TO_MOOD[q] + direction

def task_code(task: str, choices: str) -> str:
    """Convert a natural-language task to compact syllogism code, e.g. AE3."""
    p1, p2 = task.split("/")
    q1, s1, p1_obj = parse_statement(p1)
    q2, s2, p2_obj = parse_statement(p2)

    first_non_nvc = next(c for c in choices.split("|") if c != "NVC")
    _, a, c = parse_statement(first_non_nvc)
    all_terms = [s1, p1_obj, s2, p2_obj]
    middle = Counter([t for t in all_terms if t not in {a, c}]).most_common(1)[0][0]

    # Standard figure encoding for these model tables:
    # 1: a-m / m-c, 2: m-a / c-m, 3: a-m / c-m, 4: m-a / m-c
    mid_pos_1 = "S" if s1 == middle else "P"
    mid_pos_2 = "S" if s2 == middle else "P"
    figure = {("P", "S"): "1", ("S", "P"): "2", ("P", "P"): "3", ("S", "S"): "4"}[(mid_pos_1, mid_pos_2)]
    return QUANT_TO_MOOD[q1] + QUANT_TO_MOOD[q2] + figure

def hit(prediction: str, truth: str) -> float:
    """Accuracy credit. Multiple model predictions split credit equally."""
    parts = str(prediction).split(";")
    return (1.0 / len(parts)) if truth in parts else 0.0

def nvc_rule_applies(rule_name: str, syllogism: str) -> bool:
    m1, m2, fig = syllogism[0], syllogism[1], int(syllogism[2])
    if rule_name == "PartNeg":
        return m1 != "A" and m2 != "A"
    if rule_name == "EmptyStart":
        return (fig == 1 and m1 == "E") or (fig == 2 and m2 == "E")
    if rule_name == "FiguralRule":
        return fig in (3, 4)
    if rule_name == "NegativityRule":
        return m1 in ("E", "O") and m2 in ("E", "O")
    if rule_name == "Particula
[OBS t60 step 8 first 500 chars]
exit_code: 0 | --- STDOUT --- | Wrote pred_results/accuracies.csv | shape: (2240, 9) | MFA ties: 0 [] | models: ['Atmosphere', 'Conversion', 'MMT', 'Matching', 'PHM', 'PSYCOP', 'VerbalModels'] | rules: ['PartNeg', 'EmptyStart', 'FiguralRule', 'NegativityRule', 'ParticularityRule'] | rows per model/rule: | nvc           EmptyStart  FiguralRule  NegativityRule  PartNeg  ParticularityRule | model                                                                             | Atmosphere            64           64        


===== POINT 31/38: t67s2@1791614918-361358 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t67 step 2] (2944 chars)
#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
from math import sqrt

base = "CogSci_pattern_high_sim_data"
csvs = [fn for fn in sorted(os.listdir(base)) if fn.endswith(".csv")]

# Inspect exact orders and candidate similarities to decide implementation.
first_df = pd.read_csv(os.path.join(base, csvs[0]))
syll_order = first_df["Syllogism"].astype(str).tolist()
print("Syllogism order length:", len(syll_order))
print("Syllogism order:", syll_order)

responses = []
for fn in csvs:
    df = pd.read_csv(os.path.join(base, fn))
    for pred in df["Prediction"].fillna("").astype(str):
        for r in pred.split(";"):
            r = r.strip()
            if r and r not in responses:
                responses.append(r)
print("Responses first-seen:", responses)
print("Responses sorted:", sorted(responses))
std_resp = ["Aac", "Aca", "Eac", "Eca", "Iac", "Ica", "Oac", "Oca", "NVC"]
print("Std response set equals observed:", set(std_resp) == set(responses))

def vectorize(csv_path, resp_order):
    df = pd.read_csv(csv_path)
    d = dict(zip(df["Syllogism"].astype(str), df["Prediction"].fillna("").astype(str)))
    v = []
    for syll in syll_order:
        pred_set = {x.strip() for x in d[syll].split(";") if x.strip()}
        v.extend([1.0 if r in pred_set else 0.0 for r in resp_order])
    return np.array(v, dtype=float)

def cosine(a, b):
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    den = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / den) if den else np.nan

def corr(a, b):
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    aa = a - a.mean()
    bb = b - b.mean()
    den = np.linalg.norm(aa) * np.linalg.norm(bb)
    return float(np.dot(aa, bb) / den) if den else np.nan

for resp_order_name, resp_order in [("std", std_resp), ("sorted", sorted(responses)), ("firstseen", responses)]:
    print("\n=== Response order:", resp_order_name, resp_order)
    for trait in ["conscientiousness", "openness"]:
        W = np.load(os.path.join(base, f"fit_result_{trait}_W_high.npy"))
        print("\nTrait", trait, "W col norms", [np.linalg.norm(W[:, i]) for i in range(W.shape[1])], "col sums", [W[:, i].sum() for i in range(W.shape[1])])
        rows = []
        for fn in csvs:
            name = os.path.splitext(fn)[0]
            v = vectorize(os.path.join(base, fn), resp_order)
            rows.append({
                "model": name,
                "n_pred": int(v.sum()),
                "cos_col0": cosine(v, W[:,0]),
                "cos_col
[OBS t67 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- | Syllogism order length: 64 | Syllogism order: ['AA1', 'AA2', 'AA3', 'AA4', 'AI1', 'AI2', 'AI3', 'AI4', 'AE1', 'AE2', 'AE3', 'AE4', 'AO1', 'AO2', 'AO3', 'AO4', 'IA1', 'IA2', 'IA3', 'IA4', 'II1', 'II2', 'II3', 'II4', 'IE1', 'IE2', 'IE3', 'IE4', 'IO1', 'IO2', 'IO3', 'IO4', 'EA1', 'EA2', 'EA3', 'EA4', 'EI1', 'EI2', 'EI3', 'EI4', 'EE1', 'EE2', 'EE3', 'EE4', 'EO1', 'EO2', 'EO3', 'EO4', 'OA1', 'OA2', 'OA3', 'OA4', 'OI1', 'OI2', 'OI3', 'OI4', 'OE1', 'OE2', 'OE3', 'OE4', 'OO1', 


===== POINT 32/38: t67s3@1791613863-318166 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t67 step 3] (2146 chars)
import os
import numpy as np
import pandas as pd

base = "CogSci_pattern_high_sim_data"
model_files = sorted([f for f in os.listdir(base) if f.endswith(".csv")])
sylls = pd.read_csv(os.path.join(base, model_files[0]))["Syllogism"].tolist()
orders = {
    "AIEN": ["Aac","Aca","Iac","Ica","Eac","Eca","Oac","Oca","NVC"],
    "AEIN": ["Aac","Aca","Eac","Eca","Iac","Ica","Oac","Oca","NVC"],
    "alpha": ['Aac', 'Aca', 'Eac', 'Eca', 'Iac', 'Ica', 'NVC', 'Oac', 'Oca'],
}
traits = {
    "conscientiousness": np.load(os.path.join(base, "fit_result_conscientiousness_W_high.npy")),
    "openness": np.load(os.path.join(base, "fit_result_openness_W_high.npy")),
}

def vectorize(df, order, weighting):
    idx = {tok:i for i,tok in enumerate(order)}
    vec = np.zeros(64*9, dtype=float)
    for r, row in df.iterrows():
        toks = str(row["Prediction"]).split(";")
        if weighting == "binary":
            vals = {tok: 1.0 for tok in toks}
        elif weighting == "uniform":
            vals = {tok: 1.0/len(toks) for tok in toks}
        else:
            raise ValueError
        for tok, val in vals.items():
            vec[r*9 + idx[tok]] = val
    return vec

def cos(a,b):
    na=np.linalg.norm(a); nb=np.linalg.norm(b)
    return float(np.dot(a,b)/(na*nb)) if na and nb else np.nan

for order_name, order in orders.items():
    for weighting in ["binary", "uniform"]:
        print("\nAlternative:", order_name, weighting)
        rows=[]
        for mf in model_files:
            df=pd.read_csv(os.path.join(base,mf))
            v=vectorize(df, order, weighting)
            row={"model": os.path.splitext(mf)[0], "nnz": int(np.sum(v>0)), "norm": np.linalg.norm(v)}
            for trait, W in traits.items():
                comps=[cos(v,W[:,j]) for j in range(W.shape[1])]
                row[trait+"_c0"]=comps[0]
                row[trait+"_c1"]=comps[1]
                row[trait+"_max"]=max(comps)
                row[trait+"_mean"]=float(np.mean(comps))
                row[trait+"_sumvec"]=cos(v,W.sum(axis=1))
            rows.append(row)
        out=pd.DataFrame(rows)
        print(out.round(6).to_string(index=False))
[OBS t67 step 3 first 500 chars]
exit_code: 0 | --- STDOUT --- |  | Alternative: AIEN binary |        model  nnz      norm  conscientiousness_c0  conscientiousness_c1  conscientiousness_max  conscientiousness_mean  conscientiousness_sumvec  openness_c0  openness_c1  openness_max  openness_mean  openness_sumvec |   Atmosphere  128 11.313708              0.474488              0.522860               0.522860                0.498674                  0.610632     0.534766     0.112792      0.534766       0.323779         0.358701 |   Conversion


===== POINT 33/38: t67s4@1791613863-318166 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t67 step 4] (2723 chars)
import os
import numpy as np
import pandas as pd

# Paths
base_dir = "CogSci_pattern_high_sim_data"
out_dir = "pred_results"
out_path = os.path.join(out_dir, "CogSci_pattern_high_sim_data_pred.csv")
os.makedirs(out_dir, exist_ok=True)

# The 576-dimensional pattern vectors are ordered as 64 syllogisms x 9 response types.
# This order matches the structure of the supplied W_high matrices: e.g., top entries
# align with AA -> A, AI/IA -> I, AE/EA -> E, etc.
response_order = ["Aac", "Aca", "Iac", "Ica", "Eac", "Eca", "Oac", "Oca", "NVC"]

# Load high-trait pattern matrices.  Each has shape (576, 2), i.e. two latent
# high-trait patterns.  A model receives the cosine similarity of its prediction
# vector to the closest latent pattern for that trait.
trait_patterns = {
    "conscientiousness": np.load(os.path.join(base_dir, "fit_result_conscientiousness_W_high.npy")),
    "openness": np.load(os.path.join(base_dir, "fit_result_openness_W_high.npy")),
}

def prediction_vector(csv_path):
    """Convert semicolon-separated model predictions to a binary 64*9 vector."""
    df = pd.read_csv(csv_path)
    tok_to_idx = {tok: i for i, tok in enumerate(response_order)}
    vec = np.zeros(len(df) * len(response_order), dtype=float)

    for row_idx, pred in enumerate(df["Prediction"].fillna("").astype(str)):
        for tok in pred.split(";"):
            tok = tok.strip()
            if not tok:
                continue
            if tok not in tok_to_idx:
                raise ValueError(f"Unknown response token {tok!r} in {csv_path}")
            vec[row_idx * len(response_order) + tok_to_idx[tok]] = 1.0

    return vec

def cosine_similarity(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return np.nan
    return float(np.dot(a, b) / denom)

# Use a stable, human-readable model order.
model_files = ["Atmosphere.csv", "Conversion.csv", "Matching.csv", "MMT.csv",
               "PHM.csv", "PSYCOP.csv", "VerbalModels.csv"]

rows = []
for model_file in model_files:
    path = os.path.join(base_dir, model_file)
    vec = prediction_vector(path)
    model_name = os.path.splitext(model_file)[0]

    row = {"model": model_name}
    for trait, W in trait_patterns.items():
        if W.shape != (vec.size, 2):
            raise ValueError(f"Unexpected shape for {trait}: {W.shape}, expected {(vec.size, 2)}")
        component_sims = [cosine_similarity(vec, W[:, j]) for j in range(W.shape[1])]
        row[trait] = max(component_sims)

    rows.append(row)

out_df = pd.DataFrame(rows, columns=["model", "conscientiousness", "openness"])
out_df.
[OBS t67 step 4 first 500 chars]
exit_code: 0 | --- STDOUT --- | Saved: pred_results/CogSci_pattern_high_sim_data_pred.csv | Shape: (7, 3) |        model  conscientiousness  openness |   Atmosphere           0.522860  0.534766 |   Conversion           0.650358  0.645304 |     Matching           0.669315  0.433682 |          MMT           0.658485  0.688230 |          PHM           0.516571  0.466238 |       PSYCOP           0.587094  0.581916 | VerbalModels           0.749226  0.737686 |  | --- STDERR --- | 


===== POINT 34/38: t67s4@1791614918-361358 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t67 step 4] (2378 chars)
#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd

base = "CogSci_pattern_high_sim_data"
outdir = "pred_results"
os.makedirs(outdir, exist_ok=True)

# Standard syllogistic response vectorization: 64 syllogisms x 9 response options = 576.
response_order = ["Aac", "Aca", "Eac", "Eca", "Iac", "Ica", "Oac", "Oca", "NVC"]
syllogism_order = pd.read_csv(os.path.join(base, "Atmosphere.csv"))["Syllogism"].astype(str).tolist()

def vectorize_predictions(csv_path):
    df = pd.read_csv(csv_path)
    pred_by_syllogism = dict(zip(df["Syllogism"].astype(str), df["Prediction"].fillna("").astype(str)))
    vec = np.zeros(len(syllogism_order) * len(response_order), dtype=float)
    k = 0
    for syllogism in syllogism_order:
        pred_set = {x.strip() for x in pred_by_syllogism[syllogism].split(";") if x.strip()}
        for response in response_order:
            vec[k] = 1.0 if response in pred_set else 0.0
            k += 1
    return vec

def cosine_similarity(a, b):
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return np.nan
    return float(np.dot(a, b) / denom)

def trait_similarity(model_vec, W_high):
    # Each W_high file contains two high-trait pattern columns.  Compare the
    # model prediction pattern with the combined high-trait pattern.
    high_pattern = np.asarray(W_high, dtype=float).sum(axis=1)
    return cosine_similarity(model_vec, high_pattern)

model_files = sorted(fn for fn in os.listdir(base) if fn.endswith(".csv"))
trait_W = {
    "conscientiousness": np.load(os.path.join(base, "fit_result_conscientiousness_W_high.npy")),
    "openness": np.load(os.path.join(base, "fit_result_openness_W_high.npy")),
}

rows = []
for fn in model_files:
    model_name = os.path.splitext(fn)[0]
    model_vec = vectorize_predictions(os.path.join(base, fn))
    row = {"model": model_name}
    for trait, W in trait_W.items():
        row[trait] = trait_similarity(model_vec, W)
    rows.append(row)

result = pd.DataFrame(rows, columns=["model", "conscientiousness", "openness"])
outpath = os.path.join(outdir, "CogSci_pattern_high_sim_data_pred.csv")
result.to_csv(outpath, index=False)

print("Saved:", outpath)
print("Shape:", result.shape)
print(result.to_string(index=False, float_format=lambda x: f"{x:.12f}"))
[OBS t67 step 4 first 500 chars]
exit_code: 0 | --- STDOUT --- | Saved: pred_results/CogSci_pattern_high_sim_data_pred.csv | Shape: (7, 3) |        model  conscientiousness       openness |   Atmosphere     0.284604868647 0.198470576241 |   Conversion     0.391685204461 0.612498939725 |          MMT     0.440658903118 0.549547449328 |     Matching     0.241665699901 0.108121889496 |          PHM     0.260909730491 0.163492405001 |       PSYCOP     0.419404557611 0.573191799985 | VerbalModels     0.418667082487 0.636413476030 |  | --- STDERR --- | 


===== POINT 35/38: t85s1@1791613931-318581 =====
[TASK-DESC] Analyze the given saliva data and compute features that represent sample statistics or distribution (e.g., mean, location of max/min value, skewness) for each subject. Save the computed features along with subject condition as a dictionary of dictionaries into a json file "pred_results/saliva_pred.json".
[STEP-CODE t85 step 1] (784 chars)
#!/usr/bin/env python3
import os
import json
import pickle
import pandas as pd
import numpy as np

path = "saliva_data/data.pkl"
print("Exists:", os.path.exists(path))
df = pd.read_pickle(path)
print("Type:", type(df))
print("Shape:", df.shape)
print("Index:", df.index.names, type(df.index))
print("Columns:", df.columns.tolist())
print("Head:")
print(df.head(10))
print("Dtypes:")
print(df.dtypes)
print("Index levels:")
if isinstance(df.index, pd.MultiIndex):
    for name, vals in zip(df.index.names, df.index.levels):
        print(name, len(vals), list(vals)[:10])
print("Number of groups by condition/subject:")
print(df.groupby(level=["condition", "subject"]).size().head(20))
print("Total subjects:", len(df.groupby(level=["condition", "subject"])))
print("Done inspection.")
[OBS t85 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Exists: True | Type: <class 'pandas.core.frame.DataFrame'> | Shape: (154, 1) | Index: ['condition', 'subject', 'sample'] <class 'pandas.core.indexes.multi.MultiIndex'> | Columns: ['cortisol'] | Head: |                              cortisol | condition    subject sample           | Intervention Vp01    0        6.98890 |                      1        7.03320 |                      2        5.77670 |                      3        5.25790 |                      4        5.00795 |                 


===== POINT 36/38: t85s1@1791614969-361789 =====
[TASK-DESC] Analyze the given saliva data and compute features that represent sample statistics or distribution (e.g., mean, location of max/min value, skewness) for each subject. Save the computed features along with subject condition as a dictionary of dictionaries into a json file "pred_results/saliva_pred.json".
[STEP-CODE t85 step 1] (2519 chars)
#!/usr/bin/env python3
import os
import pickle
import json
import pandas as pd
import numpy as np

DATA_PATH = "saliva_data/data.pkl"
OUT_PATH = "pred_results/saliva_pred.json"

print(f"Loading {DATA_PATH} ...")
df = pd.read_pickle(DATA_PATH)
print("Loaded object type:", type(df))
print("Shape:", getattr(df, "shape", None))
print("Index names:", getattr(df.index, "names", None))
print("Columns:", list(df.columns) if hasattr(df, "columns") else None)
print("Head:")
print(df.head(10))

print("\nIndex level values/counts:")
if isinstance(df.index, pd.MultiIndex):
    for name in df.index.names:
        vals = df.index.get_level_values(name)
        print(name, "nunique=", vals.nunique(), "first=", list(pd.unique(vals)[:10]))
else:
    print(df.index[:10])

# Compute first-pass features to verify grouping.
if "cortisol" not in df.columns:
    raise ValueError("Expected a 'cortisol' column")

if isinstance(df.index, pd.MultiIndex) and {"condition", "subject", "sample"}.issubset(set(df.index.names)):
    grouped = df["cortisol"].groupby(level=["condition", "subject"])
else:
    raise ValueError("Expected MultiIndex with condition, subject, sample")

rows = []
for (condition, subject), s in grouped:
    s = s.sort_index(level="sample")
    sample_index = s.index.get_level_values("sample")
    values = pd.to_numeric(s, errors="coerce")
    max_pos = int(np.nanargmax(values.to_numpy(dtype=float)))
    min_pos = int(np.nanargmin(values.to_numpy(dtype=float)))
    row = {
        "condition": str(condition),
        "subject": str(subject),
        "n": int(values.notna().sum()),
        "argmax": int(sample_index[max_pos]),
        "argmin": int(sample_index[min_pos]),
        "mean": float(values.mean()),
        "std": float(values.std()),
        "skew": float(values.skew()),
        "kurt": float(values.kurt()),
        "min": float(values.min()),
        "max": float(values.max()),
    }
    rows.append(row)

features_df = pd.DataFrame(rows)
print("\nComputed feature preview:")
print(features_df.head())
print("\nSubjects:", len(features_df))
print("Condition counts:")
print(features_df["condition"].value_counts())

# Save a temporary preview for continuity/debugging.
os.makedirs("pred_results", exist_ok=True)
preview_path = "pred_results/saliva_pred_preview.json"
preview = {
    r["subject"]: {k: v for k, v in r.items() if k != "subject"}
    for r in rows[:5]
}
with open(preview_path, "w") as f:
    json.dump(preview, f, indent=2)
print(f"\nWrote preview JSON to {preview_path}")
[OBS t85 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loading saliva_data/data.pkl ... | Loaded object type: <class 'pandas.core.frame.DataFrame'> | Shape: (154, 1) | Index names: ['condition', 'subject', 'sample'] | Columns: ['cortisol'] | Head: |                              cortisol | condition    subject sample           | Intervention Vp01    0        6.98890 |                      1        7.03320 |                      2        5.77670 |                      3        5.25790 |                      4        5.00795 |                      5 


===== POINT 37/38: t85s2@1791613931-318581 =====
[TASK-DESC] Analyze the given saliva data and compute features that represent sample statistics or distribution (e.g., mean, location of max/min value, skewness) for each subject. Save the computed features along with subject condition as a dictionary of dictionaries into a json file "pred_results/saliva_pred.json".
[STEP-CODE t85 step 2] (2715 chars)
#!/usr/bin/env python3
import os
import json
import math
import pandas as pd
import numpy as np

INPUT_PATH = "saliva_data/data.pkl"
OUTPUT_PATH = "pred_results/saliva_pred.json"

df = pd.read_pickle(INPUT_PATH)
if not isinstance(df.index, pd.MultiIndex):
    raise ValueError("Expected a MultiIndex with levels condition, subject, sample.")
required_levels = {"condition", "subject", "sample"}
if set(df.index.names) != required_levels:
    raise ValueError(f"Expected index levels {required_levels}, got {df.index.names}.")
if "cortisol" not in df.columns:
    raise ValueError("Expected a 'cortisol' column.")

def json_safe(value):
    """Convert numpy/pandas scalar values and NaNs to JSON-compatible Python values."""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    return value

def sample_to_json_value(sample_label):
    """Represent sample location compactly; samples in this dataset are string digits."""
    if isinstance(sample_label, (np.integer, int)):
        return int(sample_label)
    if isinstance(sample_label, (np.floating, float)) and float(sample_label).is_integer():
        return int(sample_label)
    s = str(sample_label)
    if s.isdigit():
        return int(s)
    return s

results = {}

# Sort for deterministic output.
for (condition, subject), group in df.sort_index().groupby(level=["condition", "subject"], sort=True):
    series = group["cortisol"].droplevel(["condition", "subject"])
    # Ensure numerical sample order (rather than lexicographic) if labels are numeric strings.
    order = sorted(series.index, key=lambda x: int(x) if str(x).isdigit() else str(x))
    series = series.loc[order].astype(float)

    max_sample = series.idxmax()
    features = {
        "condition": str(condition),
        "argmax": sample_to_json_value(max_sample),
        "mean": json_safe(series.mean()),
        "std": json_safe(series.std()),       # pandas default ddof=1, matching standard sample statistics
        "skew": json_safe(series.skew()),     # pandas/Fisher-Pearson adjusted skewness
        "kurt": json_safe(series.kurt()),     # pandas excess kurtosis
    }
    results[str(subject)] = features

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, sort_keys=True)

print(f"Wrote {OUTPUT_PATH}")
print(f"Number of subjects: {len(results)
[OBS t85 step 2 first 500 chars]
exit_code: 0 | --- STDOUT --- | Wrote pred_results/saliva_pred.json | Number of subjects: 22 | First five subjects/features: | Vp01 {'condition': 'Intervention', 'argmax': 1, 'mean': 5.51875, 'std': 1.1545113713890678, 'skew': 0.3633256097384234, 'kurt': -1.31900226119713} | Vp03 {'condition': 'Control', 'argmax': 3, 'mean': 11.43395, 'std': 3.067824876982604, 'skew': -1.4332627692641073, 'kurt': 2.2143009983048527} | Vp05 {'condition': 'Intervention', 'argmax': 0, 'mean': 6.207607142857143, 'std': 1.52445502


===== POINT 38/38: t92s1@1791614994-362003 =====
[TASK-DESC] Computational Analysis
[STEP-CODE t92 step 1] (1487 chars)
#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np

base = Path("jnmf_visualization")
out_path = Path("pred_results/jnmf_h_importances.json")
out_path.parent.mkdir(parents=True, exist_ok=True)

W_high = np.load(base / "fit_result_conscientiousness_W_high.npy")
W_low = np.load(base / "fit_result_conscientiousness_W_low.npy")
H_high = np.load(base / "fit_result_conscientiousness_H_high.npy")
H_low = np.load(base / "fit_result_conscientiousness_H_low.npy")

print("Loaded arrays:")
print(f"  W_high shape: {W_high.shape}")
print(f"  W_low  shape: {W_low.shape}")
print(f"  H_high shape: {H_high.shape}")
print(f"  H_low  shape: {H_low.shape}")

total_H_high = float(np.sum(H_high))
total_H_low = float(np.sum(H_low))
total_H_both = total_H_high + total_H_low

scores = {
    "common error": float(1.0 - np.dot(W_high[:, 0], W_low[:, 0])),
    "common importance": float((np.sum(H_high[:, 0]) + np.sum(H_low[:, 0])) / total_H_both),
    "high importance": float(np.sum(H_high[:, 1]) / total_H_high),
    "low importance": float(np.sum(H_low[:, 1]) / total_H_low),
    "distinct error": float(np.dot(W_high[:, 1], W_low[:, 1])),
    "distinct importance": float((np.sum(H_high[:, 1]) + np.sum(H_low[:, 1])) / total_H_both),
}

with out_path.open("w", encoding="utf-8") as f:
    json.dump(scores, f, indent=2, sort_keys=True)

print("Computed scores:")
for key, value in scores.items():
    print(f"  {key}: {value:.17g}")

print(f"Saved JSON to: {out_path}")
[OBS t92 step 1 first 500 chars]
exit_code: 0 | --- STDOUT --- | Loaded arrays: |   W_high shape: (576, 2) |   W_low  shape: (576, 2) |   H_high shape: (46, 2) |   H_low  shape: (60, 2) | Computed scores: |   common error: 0.019074017463533988 |   common importance: 0.67694773029397826 |   high importance: 0.29836055701149189 |   low importance: 0.34259264124640232 |   distinct error: 0.0054058374290512894 |   distinct importance: 0.32305226970602163 | Saved JSON to: pred_results/jnmf_h_importances.json |  | --- STDERR --- | 
