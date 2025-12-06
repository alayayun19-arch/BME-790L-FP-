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
      anvil.alert("Could not fetch uploads: " + res.get("message", ""))
      return

    # Build a list of tuples (display_text, value)
    dd_items = [(u["label"], u["row_id"]) for u in res["uploads"]]

    # Assign to the DropDown (must be list of strings or tuples)
    self.drop_down_uploads.items = dd_items

    # auto-select the first item (use the tuple's value)
    if dd_items:
      self.drop_down_uploads.selected_value = dd_items[0][1]

  def button_load_click(self, **event_args):
    """
    Debugging version: calls server, prints the full response to console,
    alerts summary info, and robustly assigns items to either DataGrid or RepeatingPanel.
    """
    import anvil.server

    # 1) check selection
    row_id = getattr(self.drop_down_uploads, "selected_value", None)
    print("DEBUG: selected row_id:", row_id)
    if not row_id:
      anvil.alert("Please select an upload first. (selected_value is empty)")
      return

    # 2) call server and log the whole response
    try:
      res = anvil.server.call('load_upload_records', row_id, 200)
    except Exception as e:
      print("DEBUG: RPC call failed:", repr(e))
      anvil.alert("Server call failed: " + str(e))
      return

    print("DEBUG: server response:", res)

    if not isinstance(res, dict):
      anvil.alert("Server returned unexpected type: " + str(type(res)))
      return

    if res.get("status") != "ok":
      anvil.alert("Server error: " + res.get("message", "no message"))
      return

    # 3) examine returned records
    records = res.get("records", None)
    cols = res.get("columns", None)
    nrows = res.get("nrows", None)
    ncols = res.get("ncols", None)
    print("DEBUG: nrows:", nrows, "ncols:", ncols, "len(records):", None if records is None else len(records))
    anvil.alert(f"Server returned status OK. nrows={nrows} len(records)={len(records) if records is not None else 'None'}")

    if not records:
      anvil.alert("No records returned from server (empty list).")
      return

    # 4) detect what UI component you have and assign items
    # Try DataGrid first (common name data_grid or datagrid_1)
    assigned = False
    for grid_name in ("data_grid", "datagrid_1", "datagrid", "data_grid_1"):
      if hasattr(self, grid_name):
        grid = getattr(self, grid_name)
        try:
          grid.items = records
          print(f"DEBUG: assigned records to {grid_name}")
          assigned = True
          break
        except Exception as e:
          print(f"DEBUG: failed to set {grid_name}.items: {e}")

    # If DataGrid didn't work, use repeating_panel
    if not assigned and hasattr(self, "repeating_panel"):
      try:
        # store columns ordering for RowTemplate
        self.current_columns = cols or list(records[0].keys())
        self.repeating_panel.items = records
        print("DEBUG: assigned records to repeating_panel")
        assigned = True
      except Exception as e:
        print("DEBUG: failed to set repeating_panel.items:", e)

    if not assigned:
      anvil.alert("No grid or repeating_panel found (or assignment failed). Check component names.")
      print("DEBUG: components on form:", [(getattr(c, 'name', None), type(c).__name__) for c in self.get_components()])
      return

    # 5) success
    anvil.alert("Loaded preview: showing first rows. Columns: " + ", ".join((cols or list(records[0].keys()))[:10]))
  #Finish
  
  def form_show(self, **event_args):
    """Called when form is shown."""
    self._load_data()

  def data_grid_1_show(self, **event_args):
    """Called when the DataGrid is shown (Designer wired this)."""
    # In case the grid gets shown before form_show, ensure data is loaded
    self._load_data()

  def data_grid_2_show(self, **event_args):
    """This method is called when the data grid is shown on the screen"""
    self.columns = [{"title":"A","data_key":"A"},{"title":"B","data_key":"B"}]
    self.items = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
    pass

  def button_test_click(self, **event_args):
    """This method is called when the button is clicked"""
    try:
      res = anvil.server.call('ping')
      anvil.alert(f"ping -> {res}")
    except Exception as e:
      anvil.alert("Ping failed: " + str(e))
    pass
