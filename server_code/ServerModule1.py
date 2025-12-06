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
#import wfdb
#import matplotlib.pyplot as plt
#Changes made in Dec 4 by ShiaoXu Start
  
@anvil.server.callable
def process_csv_file(file_media, store_as="dataframe_json"):
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

  # metadata
  name = getattr(file_media, "name", "uploaded.csv")
  nrows, ncols = Cleaned_raw.shape
  uploaded_at = datetime.utcnow()

  # Option A (recommended): store DataFrame as JSON (reconstructable with orient='split')
  if store_as == "dataframe_json":
    json_str = Cleaned_raw.to_json(orient="split")  # safe, reconstructable
    row = app_tables.approach1_data.add_row(
      name=name,
      data_json=json_str,
      nrows=nrows,
      ncols=ncols,
      uploaded_at=uploaded_at
    )
    return {"status": "ok", "storage": "dataframe_json", "row_id": row.get_id()}

@anvil.server.callable
def load_dataframe_from_row(row_id):
  row = app_tables.approach1_data.get_by_id(row_id)
  if not row:
    return {"status": "error", "msg": "row not found"}

  if row.get("data_json"):
    json_str = row["data_json"]
    df = pd.read_json(json_str, orient="split")
    # DataFrame cannot be returned directly to the client; return serializable form
    return {
      "status": "ok",
      "nrows": row["nrows"],
      "ncols": row["ncols"],
      "columns": df.columns.tolist(),
      "data_records": df.to_dict(orient="records")  # list of dicts serializable to client
    }

  elif row.get("array_blob"):
    # return the blob so the client can download or re-create a numpy array
    return {
      "status": "ok",
      "array_blob": row["array_blob"],
      "nrows": row["nrows"],
      "ncols": row["ncols"]
    }

  else:
    return {"status": "error", "msg": "no data found in row"}

def save_uploaded_file(file):
  # Read uploaded CSV into pandas DataFrame
  Raw_data = pd.read_csv(BytesIO(file.get_bytes()),encoding = "ISO-8859-1")
  #missing_counts = Raw_data.isnull().sum()
  Cleaned_raw = Raw_data.dropna(axis = 1, thresh = int(0.8*len(Raw_data)))
  cols_to_drop = ['cancSpec FAMILY HISTORY',"Hdspecific FAMILY HISTORY","HTNspecific FAMILY HISTORY",
                 "Dmspecific FAMILY HISTORY","StrokeSpecific FAMILY HISTORY","OTHER","Medications",
                 "Right Eye findings","Left Eye findings"]
  Cleaned_raw = Cleaned_raw.drop(columns = cols_to_drop)  
  # Convert to list of dicts for display in DataGrid
  df_rows = Cleaned_raw.to_dict(orient = 'records')
  df_columns = list(Cleaned_raw.columns)
  return {"rows": df_rows,"columns":df_columns}

@anvil.server.callable
def list_uploaded_datasets():
  try:
    rows = []
    # <<-- CHANGE THIS to the actual table name you created:
    # If your table is named "uploaded_data" use that. If you really have approach1_data, keep it.
    table = app_tables.approach1_data   # <<<<<< check this name
    for r in table.search():
      print("Row keys:", list(r)
      rows.append({
        #"row_id": r.get_id(),
        "name":  r.get("name"),
        "nrows": r.get("nrows"),
        "ncols": r.get("ncols"),
        "uploaded_at": r.get("uploaded_at")
      })
    rows.sort(key=lambda x: x.get("uploaded_at") or datetime.min, reverse=True)
    return {"status": "ok", "uploads": rows}
  except Exception as e:
    # Print full traceback to server logs so you can inspect it in the Editor -> Logs
    print("Error in list_uploaded_datasets():", e)
    traceback.print_exc()
    return {"status": "error", "message": f"Server error: {type(e).__name__}: {e}"}
#Changes made in Dec 4 by ShiaoXu Ended

@anvil.server.callable
def store_df_in_session(result):
  # anvil.server.session is a per-user dict stored on server runtime
  anvil.server.session['df_data'] = result
  return True

@anvil.server.callable
def get_df_from_session():
  return anvil.server.session.get('df_data')