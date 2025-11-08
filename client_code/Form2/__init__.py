from ._anvil_designer import Form2Template
from anvil import *
import plotly.graph_objects as go
import anvil.server


class Form2(Form2Template):
  
  def __init__(self, df_data=None, **properties):
    self.init_components(**properties)

    if df_data and len(df_data) > 0:
      # Dynamically create columns
      cols = [{"title": k, "data_key": k} for k in df_data[0].keys()]
      self.data_grid_1.columns = cols
      self.repeating_panel_1.items = df_data


      
