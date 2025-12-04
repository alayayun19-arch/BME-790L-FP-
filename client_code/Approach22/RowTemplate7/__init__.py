from ._anvil_designer import RowTemplate7Template
from anvil import *
import anvil.server


class RowTemplate7(RowTemplate7Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
