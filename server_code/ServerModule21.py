import anvil.server
import anvil.media
import io
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ===================================================
#  helper: plot selected metrics
# ===================================================
def _plot_all_metrics_in_one(dm_dict, non_dict):

  metrics = list(dm_dict.keys())
  x = np.arange(len(metrics))

  # ---- FIX: lists require numpy functions ----
  dm_means = [np.mean(dm_dict[m]) for m in metrics]
  non_means = [np.mean(non_dict[m]) for m in metrics]

  dm_sds = [np.std(dm_dict[m], ddof=1) for m in metrics]
  non_sds = [np.std(non_dict[m], ddof=1) for m in metrics]

  fig, ax = plt.subplots(figsize=(18, 6))
  w = 0.38

  ax.bar(x - w/2, dm_means, width=w, yerr=dm_sds, capsize=4, label="DM")
  ax.bar(x + w/2, non_means, width=w, yerr=non_sds, capsize=4, label="Non-DM")

  ax.set_xticks(x)
  ax.set_xticklabels(metrics, rotation=75, ha="right")
  ax.set_ylabel("Value")
  ax.set_title("DM vs Non-DM: Selected Metrics")
  ax.legend()
  fig.tight_layout()

  buf = io.BytesIO()
  fig.savefig(buf, format="png", dpi=140)
  plt.close(fig)
  buf.seek(0)

  return anvil.BlobMedia("image/png", buf.read(), name="combined_plot.png")



# ===================================================
# 1) Main analysis function: return only TABLE and DATA
# ===================================================
@anvil.server.callable
def analyze_dm_vs_non_dm(file_media):

  csv_bytes = file_media.get_bytes()
  df = pd.read_csv(io.BytesIO(csv_bytes))

  cols = [
    "Patient ID", "HEIGHT (M)", "MASS (KG)", "BMI",
    "DM, Non-DM, STROKE",
    "global GM / ICV", "global WM / ICV", "global CSF / ICV",
    "whole brain-FA", "whole brain-MD", "whole brain-L1", "whole brain-RD",
    "wmh registered",
    "L angular gyrus-FA", "R angular gyrus-FA",
    "R postcentral gyrus-L1", "R angular gyrus-L1",
    "L postcentral gyrus-RD", "R postcentral gyrus-RD",
    "R angular gyrus-RD", "L hippocampus-RD", "R hippocampus-RD",
    "HVLT: Total Recall", "HVLT: Delayed Recall T-score",
    "HVLT: Retention % T-score", "HVLT: RDI T-score",
    "VF:T-score", "VF: # animals t-score",
    "Hb A1C%",
  ]

  df = df[[c for c in cols if c in df.columns]].copy()
  df = df.dropna(subset=["DM, Non-DM, STROKE"])
  df["Group"] = df["DM, Non-DM, STROKE"].astype(str).str.strip().str.upper()
  df_cmp = df[df["Group"].isin(["DM", "NON-DM"])]

  n_dm = sum(df_cmp["Group"] == "DM")
  n_non = sum(df_cmp["Group"] == "NON-DM")

  # ----- table computation -----
  skip = {"Patient ID", "DM, Non-DM, STROKE", "Group"}
  features = [c for c in cols if c not in skip]

  rows = []
  for col in features:
    if col not in df_cmp.columns:
      continue

    dm_vals = pd.to_numeric(df_cmp[df_cmp["Group"]=="DM"][col], errors="coerce").dropna()
    non_vals = pd.to_numeric(df_cmp[df_cmp["Group"]=="NON-DM"][col], errors="coerce").dropna()

    if len(dm_vals)==0 or len(non_vals)==0:
      rows.append({"metric": col, "dm_mean_sd": "-", "non_dm_mean_sd": "-", "p_value": "N/A"})
      continue

    stat, p = ttest_ind(dm_vals, non_vals, equal_var=False)

    rows.append({
      "metric": col,
      "dm_mean_sd": f"{dm_vals.mean():.3f} ± {dm_vals.std(ddof=1):.3f}",
      "non_dm_mean_sd": f"{non_vals.mean():.3f} ± {non_vals.std(ddof=1):.3f}",
      "p_value": f"{p:.3f}"
    })

  # ----- save arrays needed for plotting -----
  plot_features = [
    "global GM / ICV", "global WM / ICV", "global CSF / ICV",
    "whole brain-FA", "whole brain-MD", "whole brain-L1", "whole brain-RD",
    "wmh registered",
  ]

  dm_dict, non_dict = {}, {}
  for m in plot_features:
    if m in df_cmp.columns:
      dm_vals = pd.to_numeric(df_cmp[df_cmp["Group"]=="DM"][m], errors="coerce").dropna()
      non_vals = pd.to_numeric(df_cmp[df_cmp["Group"]=="NON-DM"][m], errors="coerce").dropna()
      if len(dm_vals)>0 and len(non_vals)>0:
        dm_dict[m] = dm_vals.tolist()   # <-- Converting Series → list
        non_dict[m] = non_vals.tolist() # <-- Converting Series → list

  return {
    "rows": rows,
    "n_dm": n_dm,
    "n_non": n_non,
    "dm_dict": dm_dict,
    "non_dict": non_dict,
  }


# ===================================================
# 2) generate the bar plot
# ===================================================
@anvil.server.callable
def generate_plot(dm_dict, non_dict):
  if not dm_dict or not non_dict:
    raise Exception("No data to plot. Did you run Analysis first?")
  return _plot_all_metrics_in_one(dm_dict, non_dict)
