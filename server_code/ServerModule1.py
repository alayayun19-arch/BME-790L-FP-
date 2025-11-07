import anvil.server
import pandas as pd
from io import BytesIO

@anvil.server.callable
def ping(): return "pong"
  
def process_uploaded_csv(file):
  # Read uploaded CSV into pandas DataFrame
  Raw_data = pd.read_csv(BytesIO(file.get_bytes()))
  #missing_counts = Raw_data.isnull().sum()
  Cleaned_raw = Raw_data.dropna(axis = 1, thresh = int(0.8*len(Raw_data)))
  cols_to_drop = ['cancSpec FAMILY HISTORY',"Hdspecific FAMILY HISTORY","HTNspecific FAMILY HISTORY",
                 "Dmspecific FAMILY HISTORY","StrokeSpecific FAMILY HISTORY","OTHER","Medications",
                 "Right Eye findings","Left Eye findings"]
  Cleaned_raw = Cleaned_raw.drop(columns = cols_to_drop)  
  # Optionally do some preprocessing here
  # e.g., df = df.dropna() or df.head(10)

  # Convert to list of dicts for display in DataGrid
  df_dict = Raw_data.to_dict(orient='records')
  return df_dict
