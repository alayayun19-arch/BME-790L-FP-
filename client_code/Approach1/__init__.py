from ._anvil_designer import Approach1Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.media
import anvil.users

class Approach1(Approach1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self._refresh_uploads_list()
    # Keep __init__ light; actual population runs on show
    # (Designer expects a form_show or data_grid_1_show; we'll provide both)
  #Edited by Dec 4 Start
  def _refresh_uploads_list(self):
    res = anvil.server.call('list_uploaded_datasets')
    if res.get("status") != "ok":
      anvil.alert("Could not fetch uploads: " + res.get("message",""))
      return
    dd_items = [{"label": u["label"], "value": u["row_id"]} for u in res["uploads"]]
    self.drop_down_uploads.items = dd_items
    if dd_items:
      self.drop_down_uploads.selected_value = dd_items[0]["value"]

  def button_load_click(self, **event_args):
    row_id = self.drop_down_uploads.selected_value
    if not row_id:
      anvil.alert("Select an upload")
      return
    res = anvil.server.call('load_upload_records', row_id, 200)  # preview 200 rows
    if res.get("status") != "ok":
      anvil.alert("Error: " + res.get("message",""))
      return
    records = res["records"]
    # save columns on the form so RowTemplate uses consistent order
    self.current_columns = res.get("columns", [])
    self.repeating_panel.items = records
    self.label_cols.text = ", ".join(self.current_columns[:20])
  #Finish
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
