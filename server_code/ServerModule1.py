import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import pandas as pd
from io import BytesIO
from .Form1 import Form1
from .Approach1 import Approach1
import anvil.media
import json
import numpy as np
from datetime import datetime
import traceback
import dcor
from sklearn.preprocessing import OneHotEncoder
# distance correlation library (must be available on server)
#import wfdb
#import matplotlib.pyplot as plt
#Changes made in Dec 4 by ShiaoXu Start
  
@anvil.server.callable
def process_csv_file(file_media):
  """
    file_media: the anvil Media object uploaded from the Form
    store_as: "dataframe_json" (default) or "numpy_json" or "numpy_blob"
    Returns: row id or details about saved row
    """

  # 1) Read file into pandas DataFrame
  # file_media.get_bytes() returns the file bytes
  Raw_data = pd.read_csv(BytesIO(file_media.get_bytes()),encoding = "ISO-8859-1")
  #missing_counts = Raw_data.isnull().sum()
  Cleaned_raw = Raw_data.dropna(axis = 1, thresh = int(0.8*len(Raw_data)))
  cols_to_drop = ['cancSpec FAMILY HISTORY',"Hdspecific FAMILY HISTORY","HTNspecific FAMILY HISTORY",
                  "Dmspecific FAMILY HISTORY","StrokeSpecific FAMILY HISTORY","OTHER","Medications",
                  "Right Eye findings","Left Eye findings"]
  Cleaned_raw = Cleaned_raw.drop(columns = cols_to_drop) 
  records = Cleaned_raw.to_dict(orient="records")   # list of row dicts
  columns = Cleaned_raw.columns.tolist()            # list of feature names
  return {"records": records, "columns": columns}

# ServerModule1.py  -- paste/replace into your server module

import anvil.server
import pandas as pd
import numpy as np
from io import BytesIO
import traceback

from sklearn.preprocessing import OneHotEncoder
import dcor   # ensure dcor is available in your server environment

# -------------------------
# Helper: read & clean input
# -------------------------
def read_clean_from_media(file_media):
  raw_bytes = file_media.get_bytes()
  Raw_data = pd.read_csv(BytesIO(raw_bytes), encoding="ISO-8859-1")
  # drop columns with >20% missing
  Cleaned_raw = Raw_data.dropna(axis=1, thresh=int(0.8 * len(Raw_data)))
  cols_to_drop = [
    'cancSpec FAMILY HISTORY', "Hdspecific FAMILY HISTORY", "HTNspecific FAMILY HISTORY",
    "Dmspecific FAMILY HISTORY", "StrokeSpecific FAMILY HISTORY", "OTHER", "Medications",
    "Right Eye findings", "Left Eye findings"
  ]
  Cleaned_raw = Cleaned_raw.drop(columns=[c for c in cols_to_drop if c in Cleaned_raw.columns], errors='ignore')
  return Cleaned_raw.reset_index(drop=True)

# ----------------------------------------------------
# Helper: pairing visits (your original pairing logic)
# ----------------------------------------------------
def independence_check_pairing(Cleaned_raw):
  Pair_2V = []
  Pair_8V = []
  n = len(Cleaned_raw)
  if ("patient ID" not in Cleaned_raw.columns) or ("Visit" not in Cleaned_raw.columns):
    raise ValueError("Input CSV must contain 'patient ID' and 'Visit' columns.")
  for i in range(n):
    if Cleaned_raw["Visit"].iat[i] == 8:
      break
    for j in range(i + 1, n):
      if (Cleaned_raw["patient ID"].iat[i] == Cleaned_raw["patient ID"].iat[j]) and \
      (Cleaned_raw["Visit"].iat[i] != Cleaned_raw["Visit"].iat[j]):
        Pair_2V.append(Cleaned_raw.iloc[i, :])
        Pair_8V.append(Cleaned_raw.iloc[j, :])
  Pair_2V_df = pd.DataFrame(Pair_2V).reset_index(drop=True)
  Pair_8V_df = pd.DataFrame(Pair_8V).reset_index(drop=True)
  return Pair_2V_df, Pair_8V_df

# ----------------------------
# Helper: separate numeric/cat
# ----------------------------
def separate_types(df):
  num_cols = df.select_dtypes(include=['number']).columns.tolist()
  cat_cols = df.select_dtypes(exclude=['number']).columns.tolist()
  return num_cols, cat_cols

# -----------------------------------------
# One-Hot Encoding (use sparse_output param)
# -----------------------------------------
def OHT_cat(df_target, cat_cols):
  # copy input
  df = df_target.copy()
  # normalize categorical columns to string uppercase (avoid None mix)
  for col in cat_cols:
    df[col] = df[col].astype(str).str.upper()
  if len(cat_cols) == 0:
    # ensure numeric types where possible
    return df.apply(pd.to_numeric, errors='coerce').fillna(0)

    # sklearn versions >=1.2 use sparse_output
  enc = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
  X = df[cat_cols].fillna("NAN")
  enc.fit(X)
  Y = enc.transform(X)  # numeric array
  oht_colnames = enc.get_feature_names_out(cat_cols)
  # ensure numeric dtype
  df_oht = pd.DataFrame(Y.astype(float), columns=oht_colnames, index=df.index)

  df_rest = df.drop(columns=cat_cols)
  # coerce rest to numeric where possible
  df_rest = df_rest.apply(pd.to_numeric, errors='coerce').fillna(0)
  df_combined = pd.concat([df_rest, df_oht], axis=1)
  # final coercion to numeric and fill
  df_combined = df_combined.apply(pd.to_numeric, errors='coerce').fillna(0)
  return df_combined

# ---------------------------------------------------
# Robust conversion of DataFrame -> float numpy matrix
# ---------------------------------------------------
def df_to_float_matrix(df, name=None):
  # coerce everything to numeric, convert NaN->0, return float numpy matrix
  df_numeric = df.apply(pd.to_numeric, errors='coerce').fillna(0)
  # if any object dtype remains, force all to float
  if any(df_numeric.dtypes == 'object'):
    df_numeric = df_numeric.astype(float)
  mat = df_numeric.to_numpy(dtype=float)
  return mat

# ---------------------------------------------------
# Permutation test using distance correlation (dcor)
# ---------------------------------------------------
def perm_test_dcor(arr1, arr2, n_perm=200, random_state=None):
  # ensure numeric float arrays
  a = np.asarray(arr1, dtype=float)
  b = np.asarray(arr2, dtype=float)

  # ensure 2D
  if a.ndim == 1:
    a = a.reshape((a.shape[0], 1)) if a.size else a.reshape((0,1))
  if b.ndim == 1:
    b = b.reshape((b.shape[0], 1)) if b.size else b.reshape((0,1))

  if not np.issubdtype(a.dtype, np.floating) or not np.issubdtype(b.dtype, np.floating):
    raise TypeError(f"perm_test_dcor expects numeric float arrays; got dtypes {a.dtype}, {b.dtype}")

  rng = np.random.default_rng(random_state)
  stat_obs = dcor.distance_correlation(a, b)
  perms = 0
  for _ in range(n_perm):
    b_perm = rng.permutation(b)
    stat = dcor.distance_correlation(a, b_perm)
    if stat >= stat_obs:
      perms += 1
  pval = (perms + 1) / (n_perm + 1)
  return float(stat_obs), float(pval)

# ---------------------------------------------------
# Main analysis wrapper (Task1_from_df)
# ---------------------------------------------------
def Task1_from_df(Cleaned_raw, n_perm=200, random_state=42):
  """
    Perform pairing, OHE (after dropping unwanted first column), and two dcor tests:
     - with OHE (all features)
     - numeric-only
    Returns a dict summary.
    """
  Pair_2V_df, Pair_8V_df = independence_check_pairing(Cleaned_raw)
  if Pair_2V_df.empty or Pair_8V_df.empty:
    return {"conclusion": "No paired revisit data found.", "n_pairs": 0}

    # --- DROP the first column before OHE (this avoids sample ID like 'S0030') ---
    # create OHE inputs by dropping the first column from each pair frame
  drop_col_2v = Pair_2V_df.columns[0]
  drop_col_8v = Pair_8V_df.columns[0]
  ohe_input_2V = Pair_2V_df.drop(columns=[drop_col_2v])
  ohe_input_8V = Pair_8V_df.drop(columns=[drop_col_8v])

  # find categorical columns on the reduced frames
  _, cat_cols_2V = separate_types(ohe_input_2V)
  cat_cols_2V_noid = [c for c in cat_cols_2V if c != "patient ID"]  # avoid patient ID if present
  numerized_2V = OHT_cat(ohe_input_2V, cat_cols_2V_noid)

  _, cat_cols_8V = separate_types(ohe_input_8V)
  cat_cols_8V_noid = [c for c in cat_cols_8V if c != "patient ID"]
  numerized_8V = OHT_cat(ohe_input_8V, cat_cols_8V_noid)

  # force numeric float matrices for dcor
  np_2V = df_to_float_matrix(numerized_2V, name="numerized_2V")
  np_8V = df_to_float_matrix(numerized_8V, name="numerized_8V")

  # align shapes if needed (use intersection of columns)
  if np_2V.shape[1] != np_8V.shape[1]:
    common_cols = list(set(numerized_2V.columns).intersection(set(numerized_8V.columns)))
    if len(common_cols) == 0:
      # if no common columns, make them empty matrices (stat not meaningful)
      np_2V = np.empty((np_2V.shape[0], 0), dtype=float)
      np_8V = np.empty((np_8V.shape[0], 0), dtype=float)
    else:
      numerized_2V_aligned = numerized_2V[common_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
      numerized_8V_aligned = numerized_8V[common_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
      np_2V = numerized_2V_aligned.to_numpy(dtype=float)
      np_8V = numerized_8V_aligned.to_numpy(dtype=float)

    # compute perm test for dcor (with OHE)
  stat_obs, pval = perm_test_dcor(np_2V, np_8V, n_perm=n_perm, random_state=random_state)

  # numeric-only test: select numeric columns then coerce
  num_df_2 = Pair_2V_df.select_dtypes(include=['number']).apply(pd.to_numeric, errors='coerce').fillna(0)
  num_df_8 = Pair_8V_df.select_dtypes(include=['number']).apply(pd.to_numeric, errors='coerce').fillna(0)
  if num_df_2.shape[1] == 0 or num_df_8.shape[1] == 0:
    stat_obs2, pval2 = (None, None)
  else:
    # align numeric columns
    common_num_cols = list(set(num_df_2.columns).intersection(set(num_df_8.columns)))
    if len(common_num_cols) > 0:
      np_2V_num = num_df_2[common_num_cols].to_numpy(dtype=float)
      np_8V_num = num_df_8[common_num_cols].to_numpy(dtype=float)
      stat_obs2, pval2 = perm_test_dcor(np_2V_num, np_8V_num, n_perm=n_perm, random_state=random_state)
    else:
      stat_obs2, pval2 = (None, None)

  conclusion = "Conclusion for part 1: Dependent for revisits; Cannot be considered as separate dataset"

  return {
    "conclusion": conclusion,
    "n_pairs": len(Pair_2V_df),
    "dcor_with_ohe": {"stat": stat_obs, "pval": pval},
    "dcor_numeric_only": {"stat": stat_obs2, "pval": pval2}
  }

# ---------------------------------------------------
# Server-callable wrapper
# ---------------------------------------------------
@anvil.server.callable
def independency_check(file_media, n_perm=200):
  try:
    if file_media is None:
      return {"ok": False, "error": "No file provided."}
    df = read_clean_from_media(file_media)
    res = Task1_from_df(df, n_perm=n_perm, random_state=42)
    return {"ok": True, "result": res}
  except Exception as e:
    tb = traceback.format_exc()
    return {"ok": False, "error": str(e), "traceback": tb}

