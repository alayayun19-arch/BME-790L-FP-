import anvil.server
import anvil.media
import io

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind


@anvil.server.callable
def analyze_dm_vs_non_dm(file_media):
  """
    Read uploaded CSV, run Welch's t-tests for DM vs Non-DM,
    and return:
      {
        "rows": [  # list of result rows for the DataGrid
          {
            "metric": "BMI",
            "dm_mean_sd": "29.6605 ± 4.9318",
            "non_dm_mean_sd": "25.2006 ± 6.4010",
            "p_value": 0.006369
          },
          ...
        ],
        "n_dm": 31,
        "n_non": 25
      }
    """

  # ----- 1. Read CSV into DataFrame -----
  csv_bytes = file_media.get_bytes()
  df = pd.read_csv(io.BytesIO(csv_bytes))

  # ----- 2. Select relevant columns (same as your GM_selected) -----
  cols = [
    "Patient ID",
    "HEIGHT (M)",
    "MASS (KG)",
    "BMI",
    "DM, Non-DM, STROKE",
    "global GM / ICV",
    "global WM / ICV",
    "global CSF / ICV",
    "whole brain-FA",
    "whole brain-MD",
    "whole brain-L1",
    "whole brain-RD",
    "wmh registered",
    "L hippocampus (#165) GM / ICV",
    "R hippocampus (#166) GM / ICV",
    "L angular gyrus-FA",
    "R angular gyrus-FA",
    "HVLT: Total Recall",
    "HVLT: Delayed Recall T-score",
    "HVLT: Retention % T-score",
    "HVLT: RDI T-score",
    "VF:T-score",
    "VF: # animals t-score",
    "Hb A1C%",

    # L1
    "L postcentral gyrus-L1",
    "R postcentral gyrus-L1",
    "R supramarginal gyrus-L1",
    "L angular gyrus-L1",
    "R angular gyrus-L1",
    "R hippocampus-L1",
    "L hippocampus-L1",

    # RD
    "L postcentral gyrus-RD",
    "R postcentral gyrus-RD",
    "R supramarginal gyrus-RD",
    "L angular gyrus-RD",
    "R angular gyrus-RD",
    "L hippocampus-RD",
    "R hippocampus-RD",
  ]

  existing_cols = [c for c in cols if c in df.columns]
  if len(existing_cols) == 0:
    raise Exception("None of the expected columns were found in the CSV.")

  GM_selected = df[existing_cols].copy()

  if "DM, Non-DM, STROKE" not in GM_selected.columns:
    raise Exception('"DM, Non-DM, STROKE" column is required for grouping.')

    # Simple cleaning: drop rows without group label
  GM_clean = GM_selected.dropna(subset=["DM, Non-DM, STROKE"]).copy()

  # ----- 3. Build group column and keep only DM / Non-DM -----
  df_cmp = GM_clean.copy()
  df_cmp["Group"] = (
    df_cmp["DM, Non-DM, STROKE"]
      .astype(str)
      .str.strip()
      .str.upper()
  )
  df_cmp = df_cmp[df_cmp["Group"].isin(["DM", "NON-DM"])].copy()

  group_counts = df_cmp["Group"].value_counts()
  n_dm = int(group_counts.get("DM", 0))
  n_non = int(group_counts.get("NON-DM", 0))

  # ----- 4. Features to compare (same order as your notebook) -----
  features = [
    "Patient ID",
    "HEIGHT (M)", "MASS (KG)", "BMI", "DM, Non-DM, STROKE", "Hb A1C%",
    "global GM / ICV", "global WM / ICV", "global CSF / ICV",
    "whole brain-FA", "whole brain-MD", "whole brain-L1", "whole brain-RD",
    "wmh registered",
    "L angular gyrus-FA", "R angular gyrus-FA",
    "R postcentral gyrus-L1",
    "R angular gyrus-L1",
    "L postcentral gyrus-RD",
    "R postcentral gyrus-RD",
    "R angular gyrus-RD", "L hippocampus-RD", "R hippocampus-RD",
    "HVLT: Total Recall", "HVLT: Delayed Recall T-score",
    "HVLT: Retention % T-score", "HVLT: RDI T-score",
    "VF:T-score", "VF: # animals t-score",
  ]
  # Optional hippocampus GM / ICV column
  features.insert(features.index("L angular gyrus-FA"), "hippocampus GM / ICV")

  skip_cols = {"Patient ID", "DM, Non-DM, STROKE", "Group"}

  rows = []

  # ----- 5. Loop over features and run Welch's t-test -----
  for col in features:
    if col in skip_cols:
      continue

    if col not in df_cmp.columns:
      rows.append({
        "metric": col,
        "dm_mean_sd": "-",
        "non_dm_mean_sd": "-",
        "p_value": None
      })
      continue

    dm_vals = pd.to_numeric(
      df_cmp.loc[df_cmp["Group"] == "DM", col],
      errors="coerce"
    )
    non_vals = pd.to_numeric(
      df_cmp.loc[df_cmp["Group"] == "NON-DM", col],
      errors="coerce"
    )

    dm_clean = dm_vals.dropna()
    non_clean = non_vals.dropna()

    if len(dm_clean) == 0 or len(non_clean) == 0:
      rows.append({
        "metric": col,
        "dm_mean_sd": "-",
        "non_dm_mean_sd": "-",
        "p_value": None
      })
      continue

      # Welch's t-test
    stat, p = ttest_ind(
      dm_clean, non_clean,
      equal_var=False,
      nan_policy="omit"
    )

    dm_str = f"{dm_clean.mean():.3f} ± {dm_clean.std(ddof=1):.3f}"
    non_str = f"{non_clean.mean():.3f} ± {non_clean.std(ddof=1):.3f}"
    p_fmt = f"{p:.3f}" if p is not None and not np.isnan(p) else "N/A"

    rows.append({
      "metric": col,
      "dm_mean_sd": dm_str,
      "non_dm_mean_sd": non_str,
      "p_value": p_fmt
    })


  return {
    "rows": rows,
    "n_dm": n_dm,
    "n_non": n_non
  }
