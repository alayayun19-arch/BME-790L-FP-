import anvil.server
import io
import pandas as pd
import numpy as np
import re
import statsmodels.formula.api as smf


@anvil.server.callable
def analyze_dti_cognition(file_media):
  """
  Runs regression models: outcome ~ ROI + HbA1C + WMH + BMI
  Only DM subjects are included.
  Returns formatted tables for front-end display.
  """

  # -------------------------------------------------------
  # 1. Load CSV
  # -------------------------------------------------------
  df = pd.read_csv(io.BytesIO(file_media.get_bytes()), sep=None, engine="python")
  df.columns = df.columns.str.strip()

  if "VF: # animals t-score" in df.columns:
    df = df.rename(columns={"VF: # animals t-score": "VF_animals_T"})

  # -------------------------------------------------------
  # 2. Keep DM only
  # -------------------------------------------------------
  df["Group"] = df["DM, Non-DM, STROKE"].astype(str).str.upper().str.strip()
  df_dm = df[df["Group"] == "DM"].drop(columns=["Group"]).copy()

  # -------------------------------------------------------
  # 3. Define outcomes/predictors
  # -------------------------------------------------------
  outcomes = {
    "HVLT Total Score": "HVLT: Total Recall",
    "VF animals T score": "VF_animals_T",
  }

  roi_predictors = [
    "whole brain-FA", "whole brain-MD", "whole brain-L1", "whole brain-RD",
    "L postcentral gyrus-L1","R postcentral gyrus-L1","R supramarginal gyrus-L1",
    "L angular gyrus-L1","R angular gyrus-L1","R hippocampus-L1","L hippocampus-L1",
    "L postcentral gyrus-RD","R postcentral gyrus-RD","R supramarginal gyrus-RD",
    "L angular gyrus-RD","R angular gyrus-RD","L hippocampus-RD","R hippocampus-RD",
  ]

  covars = ["Hb A1C%", "wmh registered", "BMI"]


  # -------------------------------------------------------
  # 4. Safe renaming for StatsModels
  # -------------------------------------------------------
  def to_safe(name):
    s = re.sub(r'[^A-Za-z0-9_]+', '_', str(name)).strip('_')
    s = re.sub(r'_+', '_', s)
    if not s:
      s = "col"
    if re.match(r'^\d', s):
      s = "_" + s
    return s

  need_cols = list(set(list(outcomes.values()) + roi_predictors + covars))

  safe_map = {}
  used = set()

  for col in need_cols:
    if col not in df_dm.columns:
      continue
    base = to_safe(col)
    new = base
    i = 1
    while new in used:
      i += 1
      new = f"{base}_{i}"
    safe_map[col] = new
    used.add(new)

  df2 = df_dm.rename(columns=safe_map).copy()

  # Convert numeric
  for col in need_cols:
    if col in safe_map:
      df2[safe_map[col]] = pd.to_numeric(df2[safe_map[col]], errors="coerce")

  # -------------------------------------------------------
  # 5. Model fitting
  # -------------------------------------------------------
  def fit_model(y_orig, x_orig):
    if y_orig not in safe_map or x_orig not in safe_map:
      return dict(p=np.nan, r2_adj=np.nan)

    y = safe_map[y_orig]
    x = safe_map[x_orig]
    covs = [safe_map[c] for c in covars if c in safe_map]

    dd = df2[[y, x] + covs].dropna()
    if len(dd) < 10:
      return dict(p=np.nan, r2_adj=np.nan)

    model = smf.ols(f"{y} ~ {x} + " + " + ".join(covs), data=dd).fit()

    return dict(
      p=model.pvalues.get(x, np.nan),
      r2_adj=model.rsquared_adj
    )

  # -------------------------------------------------------
  # 6. Run models + format results
  # -------------------------------------------------------
  rows = []
  for outcome_label, outcome_col in outcomes.items():
    for roi in roi_predictors:

      if outcome_col not in df_dm.columns or roi not in df_dm.columns:
        result = dict(p=np.nan, r2_adj=np.nan)
      else:
        result = fit_model(outcome_col, roi)

      p_val = result["p"]
      r2 = result["r2_adj"]

      # --- format three decimals as STRING ---
      p_fmt = "" if np.isnan(p_val) else f"{p_val:.3f}"
      r2_fmt = "" if np.isnan(r2) else f"{r2:.3f}"

      rows.append({
        "outcome": outcome_label,
        "roi": roi,
        "p": p_fmt,
        "r2_adj": r2_fmt
      })

  df_res = pd.DataFrame(rows)

  # -------------------------------------------------------
  # 7. Output tables
  # -------------------------------------------------------
  hvlt_table = df_res[df_res["outcome"] == "HVLT Total Score"][["roi", "p", "r2_adj"]]
  vf_table   = df_res[df_res["outcome"] == "VF animals T score"][["roi", "p", "r2_adj"]]

  return {
    "hvlt_table": hvlt_table.to_dict(orient="records"),
    "vf_table":   vf_table.to_dict(orient="records"),
  }
