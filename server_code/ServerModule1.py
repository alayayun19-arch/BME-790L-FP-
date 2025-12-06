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

'''def save_uploaded_file(file):
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
  return {"rows": df_rows,"columns":df_columns}'''

@anvil.server.callable
def list_uploaded_datasets():
  """
    Return a list of upload summaries (one per DB row that looks like an upload).
    Each returned item is: {label, row_id, nrows, ncols, uploaded_at}
    """
  try:
    # Change this name if your uploads table is different
    table_name = "approach1_data"   # <- use the table that contains the rows you printed
    if not hasattr(app_tables, table_name):
      avail = [n for n in dir(app_tables) if not n.startswith("_")]
      return {"status": "error", "message": f"Table '{table_name}' not found. Available tables: {avail}"}

    table = getattr(app_tables, table_name)

    uploads = []
    for r in table.search():
      try:
        row_id = r.get_id()
      except Exception:
        row_id = None

        # Use safe .get with default None to avoid the 'get' quirk on missing fields
      name = r.get("name") if "name" in r else (r.get("processed_name") if "processed_name" in r else None)
      nrows = r.get("nrows") if "nrows" in r else None
      ncols = r.get("ncols") if "ncols" in r else None
      uploaded_at = r.get("uploaded_at") if "uploaded_at" in r else None

      label = name or f"Upload {row_id}"
      # Append summary
      uploads.append({
        "label": label,
        "row_id": row_id,
        "nrows": nrows,
        "ncols": ncols,
        "uploaded_at": uploaded_at
      })

      # sort by uploaded_at if present (newest first)
    uploads.sort(key=lambda x: x.get("uploaded_at") or datetime.min, reverse=True)

    return {"status": "ok", "uploads": uploads}

  except Exception as e:
    traceback.print_exc()
    return {"status": "error", "message": f"{type(e).__name__}: {e}"}

    def load_upload_records(row_id, max_rows=200):
      """
    Given an upload-row id (from list_uploaded_datasets), parse its data_json and
    return up to max_rows records as a list of dicts for the client to display.
    """
    try:
      # same table used earlier
      table_name = "approach1_data"   # change if your upload row is in another table
      table = getattr(app_tables, table_name)
      row = table.get_by_id(row_id)
      if row is None:
        return {"status": "error", "message": "Row not found"}

      data_json = row.get("data_json")
      if not data_json:
        return {"status": "error", "message": "No data_json found in this row"}

        # Parse pandas orient='split' JSON
      try:
        df = pd.read_json(data_json, orient="split")
      except Exception:
        # fallback: maybe it's a JSON string containing the structure
        try:
          obj = json.loads(data_json)
          # try DataFrame from obj (if obj has "data" and "columns")
          if isinstance(obj, dict) and "data" in obj and "columns" in obj:
            df = pd.DataFrame(obj["data"], columns=obj["columns"])
          else:
            # last-resort: try constructing DataFrame directly
            df = pd.DataFrame(obj)
        except Exception as e2:
          return {"status": "error", "message": f"Failed to parse data_json: {e2}"}

        # Limit rows for preview if requested
      if max_rows is not None:
        df = df.iloc[:int(max_rows)]

      records = df.to_dict(orient="records")
      columns = df.columns.tolist()
      return {"status": "ok", "columns": columns, "records": records, "nrows": df.shape[0], "ncols": df.shape[1]}

    except Exception as e:
      traceback.print_exc()
      return {"status": "error", "message": f"{type(e).__name__}: {e}"}
#Changes made in Dec 4 by ShiaoXu Ended

@anvil.server.callable
def store_df_in_session(result):
  # anvil.server.session is a per-user dict stored on server runtime
  anvil.server.session['df_data'] = result
  return True

@anvil.server.callable
def get_df_from_session():
  return anvil.server.session.get('df_data')