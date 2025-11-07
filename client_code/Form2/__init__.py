from ._anvil_designer import Form2Template
from anvil import *
import anvil.server

class Form2(Form2Template):
  def __init__(self, df_data=None, **properties):
    self.init_components(**properties)

    if df_data:
      # Assign data to the repeating panel
      self.repeating_panel_1.items = df_data
      
  def data_grid_1_show(self, **event_args):
    """This method is called when the data grid is shown on the screen"""
    pass
