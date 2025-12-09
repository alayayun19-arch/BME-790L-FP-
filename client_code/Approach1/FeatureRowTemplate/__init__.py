from ._anvil_designer import FeatureRowTemplateTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


class FeatureRowTemplate(FeatureRowTemplateTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    # debug
    print("RowTemplate __init__ properties keys:", list(properties.keys())[:10])

    # Prefer attribute, fall back to item['_columns']
    cols = getattr(self, "columns", None)
    if not cols:
      cols = self.item.get("_columns", [])

    print("RowTemplate: columns passed:", len(cols))

    if not hasattr(self, "flow_panel_1"):
      raise RuntimeError("RowTemplate: flow_panel_1 missing in designer")

    self.flow_panel_1.clear()

    for col in cols:
      val = self.item.get(col, "")
      lbl = Label(text=str(val), tooltip=col)
      lbl.width = "120px"
      lbl.wrap = False
      self.flow_panel_1.add_component(lbl)