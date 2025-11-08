import anvil.server
import pandas as pd
from io import BytesIO
from .Form1 import Form1
from .Form2 import Form2

import wfdb
import numpy as np
import matplotlib.pyplot as plt

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
  print(Cleaned_raw.head())
  # Convert to list of dicts for display in DataGrid
  df_dict = Cleaned_raw.to_dict(orient='records')
  return df_dict
