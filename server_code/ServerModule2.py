# import anvil.server
# import anvil.media
# import io

# import numpy as np
# import pandas as pd
# # from scipy.stats import ttest_ind

# # For plotting
# import matplotlib
# matplotlib.use("Agg")     # Use non-GUI backend on the server
# import matplotlib.pyplot as plt


# # generic DM vs Non-DM domain analysis 
# def _compute_domain_table_and_plot(df, region_cols, ylabel, title):
#   """
#   Run DM vs Non-DM comparison for a set of brain regions,
#   and (if possible) generate a bar plot.

#   Parameters
#   ----------
#   df : pd.DataFrame
#       Full dataframe read from the CSV (must contain 'DM, Non-DM, STROKE').
#   region_cols : list[str]
#       Column names for this domain (GM / WM / CSF / WMH).
#   ylabel : str
#       Y-axis label for the bar plot (e.g. 'GM / ICV').
#   title : str
#       Title for the bar plot.

#   Returns
#   -------
#   rows : list[dict]
#       Each row has keys: metric, dm_mean_sd, non_dm_mean_sd, p_value.
#   plot_media : anvil.BlobMedia or None
#       PNG image with the bar plot, or None if plotting fails / no data.
#   """
#   # Keep only region columns that actually exist in the dataframe
#   existing_regions = [c for c in region_cols if c in df.columns]

#   if "DM, Non-DM, STROKE" not in df.columns or len(existing_regions) == 0:
#     return [], None

#   # Subset to group column + region columns
#   df_cmp = df[["DM, Non-DM, STROKE"] + existing_regions].copy()
#   df_cmp["Group"] = df_cmp["DM, Non-DM, STROKE"].astype(str).str.strip().str.upper()
#   df_cmp = df_cmp[df_cmp["Group"].isin(["DM", "NON-DM"])].copy()

#   if df_cmp.empty:
#     return [], None

#   rows = []
#   dm_means, non_means = [], []
#   dm_stds, non_stds = [], []
#   reg_labels = []

#   for col in existing_regions:
#     dm_vals = pd.to_numeric(
#       df_cmp.loc[df_cmp["Group"] == "DM", col],
#       errors="coerce"
#     ).dropna()
#     non_vals = pd.to_numeric(
#       df_cmp.loc[df_cmp["Group"] == "NON-DM", col],
#       errors="coerce"
#     ).dropna()

#     # If no numeric data in one group, just put dashes
#     if len(dm_vals) == 0 or len(non_vals) == 0:
#       rows.append({
#         "metric": col,
#         "dm_mean_sd": "-",
#         "non_dm_mean_sd": "-",
#         "p_value": "N/A"
#       })
#       continue

#     stat, p = ttest_ind(dm_vals, non_vals, equal_var=False, nan_policy="omit")

#     dm_mean, dm_sd = dm_vals.mean(), dm_vals.std(ddof=1)
#     non_mean, non_sd = non_vals.mean(), non_vals.std(ddof=1)

#     dm_means.append(dm_mean)
#     non_means.append(non_mean)
#     dm_stds.append(dm_sd)
#     non_stds.append(non_sd)
#     reg_labels.append(col)

#     dm_str = f"{dm_mean:.3f} ± {dm_sd:.3f}"
#     non_str = f"{non_mean:.3f} ± {non_sd:.3f}"
#     p_fmt = f"{p:.3f}" if p is not None and not np.isnan(p) else "N/A"

#     rows.append({
#       "metric": col,
#       "dm_mean_sd": dm_str,
#       "non_dm_mean_sd": non_str,
#       "p_value": p_fmt
#     })

#   # Build bar plot if we have at least one valid region
#   plot_media = None
#   if len(reg_labels) > 0:
#     try:
#       x = np.arange(len(reg_labels))
#       w = 0.38

#       fig, ax = plt.subplots(figsize=(12, 5))
#       ax.bar(x - w/2, dm_means,  width=w, yerr=dm_stds,  capsize=3, label="DM")
#       ax.bar(x + w/2, non_means, width=w, yerr=non_stds, capsize=3, label="Non-DM")
#       ax.set_xticks(x)
#       ax.set_xticklabels(reg_labels, rotation=45, ha="right")
#       ax.set_ylabel(ylabel)
#       ax.set_title(title)
#       ax.legend()
#       fig.tight_layout()

#       buf = io.BytesIO()
#       fig.savefig(buf, format="png", dpi=150)
#       plt.close(fig)
#       buf.seek(0)

#       plot_media = anvil.BlobMedia("image/png", buf.read(), name=f"{title}.png")
#     except Exception:
#       # If anything goes wrong, simply return no plot
#       plot_media = None

#   return rows, plot_media


# # ---------- Main callable: demographics + GM/WM/CSF/WMH ----------
# @anvil.server.callable
# def analyze_dm_vs_non_dm(file_media):
#   """
#   Read uploaded CSV, run:
#     1) Demographic / global Welch's t-tests (original table)
#     2) GM domain analysis (table + bar plot)
#     3) WM domain analysis
#     4) CSF domain analysis
#     5) WMH domain analysis

#   Returns a dict with:
#     - rows, n_dm, n_non
#     - gm_rows, gm_plot
#     - wm_rows, wm_plot
#     - csf_rows, csf_plot
#     - wmh_rows, wmh_plot
#   """

#   # ----- 1. Read CSV into a DataFrame -----
#   csv_bytes = file_media.get_bytes()
#   df = pd.read_csv(io.BytesIO(csv_bytes))

#   # ----- 2. Columns used in the original demographics/global analysis -----
#   cols = [
#     "Patient ID",
#     "HEIGHT (M)",
#     "MASS (KG)",
#     "BMI",
#     "DM, Non-DM, STROKE",
#     "global GM / ICV",
#     "global WM / ICV",
#     "global CSF / ICV",
#     "whole brain-FA",
#     "whole brain-MD",
#     "whole brain-L1",
#     "whole brain-RD",
#     "wmh registered",
#     "L hippocampus (#165) GM / ICV",
#     "R hippocampus (#166) GM / ICV",
#     "L angular gyrus-FA",
#     "R angular gyrus-FA",
#     "HVLT: Total Recall",
#     "HVLT: Delayed Recall T-score",
#     "HVLT: Retention % T-score",
#     "HVLT: RDI T-score",
#     "VF:T-score",
#     "VF: # animals t-score",
#     "Hb A1C%",

#     # L1
#     "L postcentral gyrus-L1",
#     "R postcentral gyrus-L1",
#     "R supramarginal gyrus-L1",
#     "L angular gyrus-L1",
#     "R angular gyrus-L1",
#     "R hippocampus-L1",
#     "L hippocampus-L1",

#     # RD
#     "L postcentral gyrus-RD",
#     "R postcentral gyrus-RD",
#     "R supramarginal gyrus-RD",
#     "L angular gyrus-RD",
#     "R angular gyrus-RD",
#     "L hippocampus-RD",
#     "R hippocampus-RD",
#   ]

#   existing_cols = [c for c in cols if c in df.columns]
#   if len(existing_cols) == 0:
#     raise Exception("None of the expected columns were found in the CSV.")

#   GM_selected = df[existing_cols].copy()

#   if "DM, Non-DM, STROKE" not in GM_selected.columns:
#     raise Exception('"DM, Non-DM, STROKE" column is required for grouping.')

#   # Drop rows without group label
#   GM_clean = GM_selected.dropna(subset=["DM, Non-DM, STROKE"]).copy()

#   # ----- 3. Build group column and keep DM / Non-DM -----
#   df_cmp = GM_clean.copy()
#   df_cmp["Group"] = (
#     df_cmp["DM, Non-DM, STROKE"]
#       .astype(str)
#       .str.strip()
#       .str.upper()
#   )
#   df_cmp = df_cmp[df_cmp["Group"].isin(["DM", "NON-DM"])].copy()

#   group_counts = df_cmp["Group"].value_counts()
#   n_dm = int(group_counts.get("DM", 0))
#   n_non = int(group_counts.get("NON-DM", 0))

#   # ----- 4. Original feature list for demographics/global table -----
#   features = [
#     "Patient ID",
#     "HEIGHT (M)", "MASS (KG)", "BMI", "DM, Non-DM, STROKE", "Hb A1C%",
#     "global GM / ICV", "global WM / ICV", "global CSF / ICV",
#     "whole brain-FA", "whole brain-MD", "whole brain-L1", "whole brain-RD",
#     "wmh registered",
#     "L angular gyrus-FA", "R angular gyrus-FA",
#     "R postcentral gyrus-L1",
#     "R angular gyrus-L1",
#     "L postcentral gyrus-RD",
#     "R postcentral gyrus-RD",
#     "R angular gyrus-RD", "L hippocampus-RD", "R hippocampus-RD",
#     "HVLT: Total Recall", "HVLT: Delayed Recall T-score",
#     "HVLT: Retention % T-score", "HVLT: RDI T-score",
#     "VF:T-score", "VF: # animals t-score",
#   ]
#   # Optional: hippocampus GM / ICV
#   if "hippocampus GM / ICV" not in features:
#     features.insert(features.index("L angular gyrus-FA"), "hippocampus GM / ICV")

#   skip_cols = {"Patient ID", "DM, Non-DM, STROKE", "Group"}

#   rows = []

#   # ----- 5. Loop over features and run Welch's t-test (table shown in DataGrid) -----
#   for col in features:
#     if col in skip_cols:
#       continue

#     if col not in df_cmp.columns:
#       rows.append({
#         "metric": col,
#         "dm_mean_sd": "-",
#         "non_dm_mean_sd": "-",
#         "p_value": "N/A"
#       })
#       continue

#     dm_vals = pd.to_numeric(
#       df_cmp.loc[df_cmp["Group"] == "DM", col],
#       errors="coerce"
#     ).dropna()
#     non_vals = pd.to_numeric(
#       df_cmp.loc[df_cmp["Group"] == "NON-DM", col],
#       errors="coerce"
#     ).dropna()

#     if len(dm_vals) == 0 or len(non_vals) == 0:
#       rows.append({
#         "metric": col,
#         "dm_mean_sd": "-",
#         "non_dm_mean_sd": "-",
#         "p_value": "N/A"
#       })
#       continue

#     stat, p = ttest_ind(dm_vals, non_vals, equal_var=False, nan_policy="omit")

#     dm_str = f"{dm_vals.mean():.3f} ± {dm_vals.std(ddof=1):.3f}"
#     non_str = f"{non_vals.mean():.3f} ± {non_vals.std(ddof=1):.3f}"
#     p_fmt = f"{p:.3f}" if p is not None and not np.isnan(p) else "N/A"

#     rows.append({
#       "metric": col,
#       "dm_mean_sd": dm_str,
#       "non_dm_mean_sd": non_str,
#       "p_value": p_fmt
#     })

#   # ------------------------------------------------------------------
#   # 6. Domain-level analyses: GM / WM / CSF / WMH
#   # ------------------------------------------------------------------

#   # 6.1 Grey matter (GM)
#   gm_region_cols = [
#     "global GM / ICV",
#     "L Frontal Lobe GM / ICV", "R Frontal Lobe GM / ICV",
#     "L Parietal Lobe GM / ICV", "R Parietal Lobe GM / ICV",
#     "L Occipital Lobe GM / ICV", "R Occipital Lobe GM / ICV",
#     "L Temporal Lobe GM / ICV", "R Temporal Lobe GM / ICV",
#     "cerebellum (#181) GM / ICV",
#     "brainstem (#182) GM / ICV",
#   ]
#   gm_rows, gm_plot = _compute_domain_table_and_plot(
#     df,
#     gm_region_cols,
#     ylabel="GM / ICV",
#     title="DM vs Non-DM: Global and Regional GM (normalized by ICV)"
#   )

#   # 6.2 White matter (WM)
#   wm_region_cols = [
#     "global WM / ICV",
#     "L Frontal Lobe WM / ICV", "R Frontal Lobe WM / ICV",
#     "L Parietal Lobe WM / ICV", "R Parietal Lobe WM / ICV",
#     "L Occipital Lobe WM / ICV", "R Occipital Lobe WM / ICV",
#     "L Temporal Lobe WM / ICV", "R Temporal Lobe WM / ICV",
#     "cerebellum (#181) WM / ICV",
#     "brainstem (#182) WM / ICV",
#   ]
#   wm_rows, wm_plot = _compute_domain_table_and_plot(
#     df,
#     wm_region_cols,
#     ylabel="WM / ICV",
#     title="DM vs Non-DM: Global and Regional WM (normalized by ICV)"
#   )

#   # 6.3 CSF
#   csf_region_cols = [
#     "global CSF / ICV",
#     "L Frontal Lobe CSF / ICV", "R Frontal Lobe CSF / ICV",
#     "L Parietal Lobe CSF / ICV", "R Parietal Lobe CSF / ICV",
#     "L Occipital Lobe CSF / ICV", "R Occipital Lobe CSF / ICV",
#     "L Temporal Lobe CSF / ICV", "R Temporal Lobe CSF / ICV",
#     "cerebellum (#181) CSF / ICV",
#     "brainstem (#182) CSF / ICV",
#   ]
#   csf_rows, csf_plot = _compute_domain_table_and_plot(
#     df,
#     csf_region_cols,
#     ylabel="CSF / ICV",
#     title="DM vs Non-DM: Global and Regional CSF (normalized by ICV)"
#   )

#   # 6.4 WMH
#   wmh_region_cols = [
#     "wmh unregistered",
#     "L Frontal Lobe WMHs / ICV", "R Frontal Lobe WMHs / ICV",
#     "L Parietal Lobe WMHs / ICV", "R Parietal Lobe WMHs / ICV",
#     "L Occipital Lobe WMHs / ICV", "R Occipital Lobe WMHs / ICV",
#     "L Temporal Lobe WMHs / ICV", "R Temporal Lobe WMHs / ICV",
#     "cerebellum (#181) WMHs / ICV",
#     "brainstem (#182) WMHs / ICV",
#   ]
#   wmh_rows, wmh_plot = _compute_domain_table_and_plot(
#     df,
#     wmh_region_cols,
#     ylabel="WMHs / ICV",
#     title="DM vs Non-DM: Regional WMH burden"
#   )

#   # ----- 7. Return everything to the client -----
#   return {
#     "rows": rows,
#     "n_dm": n_dm,
#     "n_non": n_non,

#     "gm_rows": gm_rows,
#     "gm_plot": gm_plot,

#     "wm_rows": wm_rows,
#     "wm_plot": wm_plot,

#     "csf_rows": csf_rows,
#     "csf_plot": csf_plot,

#     "wmh_rows": wmh_rows,
#     "wmh_plot": wmh_plot,
#   }

