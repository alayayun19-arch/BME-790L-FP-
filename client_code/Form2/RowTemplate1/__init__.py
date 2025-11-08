from ._anvil_designer import RowTemplate1Template
from anvil import *
import anvil.server


class RowTemplate1(RowTemplate1Template):
  def __init__(self,item, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    '''try:
      self.cells_panel.clear()
    except Exception:
      pass'''

    # Get column order from parent form (Form2)
    parent = self.get_open_form()
    columns = getattr(parent, "df_columns", list(item.keys()))

    # For each column, create a label (or use existing controls if you designed them)
    for col in columns:
      val = item.get(col, "")
      # Create a small panel for name/value or just a Label for the value (since headers are in DataGrid)
      lbl = Label(text=str(val))
      # If you want to attach a tooltip with the column name:
      lbl.tooltip = col
      # Adjust width/style if needed; add to container
      # If your template is designed with fixed cell labels, set those instead of creating new ones
      # Example: self.cells_panel is a LinearPanel in the template
      self.cells_panel.add_component(lbl)

    # Any code you write here will run before the form opens.
