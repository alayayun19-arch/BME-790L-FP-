from ._anvil_designer import Form2Template
from anvil import *
import anvil.server

class Form2(Form2Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    
    # Keep __init__ light; actual population runs on show
    # (Designer expects a form_show or data_grid_1_show; we'll provide both)

  def form_show(self, **event_args):
    """Called when form is shown."""
    self._load_data()

  def data_grid_1_show(self, **event_args):
    """Called when the DataGrid is shown (Designer wired this)."""
    # In case the grid gets shown before form_show, ensure data is loaded
    self._load_data()

  def _load_data(self):
    '''# Avoid loading multiple times
    if getattr(self, "_loaded", False):
      return
    result = anvil.server.call('get_df_from_session')
    if not result:
      print("No result in session")
      return

    df_rows = result.get('rows', [])
    df_columns = result.get('columns', [])
    if not df_rows:
      print("No rows to display")
      return

    # Save columns on the form for RowTemplate1 to use
    self.df_columns = df_columns
    # Build DataGrid columns in the explicit order from server
    cols = [{"title": c, "data_key": c} for c in df_columns]
    self.data_grid_1.columns = cols
    try:
      self.repeating_panel_1.items = df_rows
    except Exception:
      # fallback: set items on the data_grid itself
      self.data_grid_1.items = df_rows

    print("Loaded rows:", len(df_rows))
    self._loaded = True'''
    self.data_grid_1.columns = [{"title":"A","data_key":"A"},{"title":"B","data_key":"B"}]
    self.data_grid_1.items = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
    print("Sanity test set items -> should show 2 rows")

  def data_grid_2_show(self, **event_args):
    """This method is called when the data grid is shown on the screen"""
    self.columns = [{"title":"A","data_key":"A"},{"title":"B","data_key":"B"}]
    self.items = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
    pass
