from ._anvil_designer import Approach3Template
from anvil import *
import anvil.server

class Approach3(Approach3Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def outlined_button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('Form1')
    pass
