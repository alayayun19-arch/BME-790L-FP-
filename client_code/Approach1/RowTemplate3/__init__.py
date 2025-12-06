from ._anvil_designer import RowTemplate3Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


class RowTemplate3(RowTemplate3Template):
  def __init__(self, item=None, **properties):
    self.init_components(**properties)
    self.container_panel.clear()
    if not item:
      return
      # get columns ordering from parent form if available
    cols = getattr(self.parent, "current_columns", list(item.keys()))
    # create a label for each column value (horizontal)
    for k in cols:
      val = item.get(k, "")
      lbl = anvil.Label(text=str(val), padding="4px")
      self.container_panel.add_component(lbl)