from ._anvil_designer import Approach22Template
from anvil import *
import plotly.graph_objects as go
import anvil.server


class Approach22(Approach22Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def file_loader_1_copy_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    pass
