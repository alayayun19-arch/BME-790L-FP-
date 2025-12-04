import anvil.server
import pandas as pd
from io import BytesIO
from .Form1 import Form1
from .Approach1 import Approach1

#import wfdb
import numpy as np
#import matplotlib.pyplot as plt

@anvil.server.callable
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
def store_df_in_session(result):
  # anvil.server.session is a per-user dict stored on server runtime
  anvil.server.session['df_data'] = result
  return True

@anvil.server.callable
def get_df_from_session():
  return anvil.server.session.get('df_data')