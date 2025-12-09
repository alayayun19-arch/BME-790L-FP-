from ._anvil_designer import Approach22Template
from anvil import *
import plotly.graph_objects as go
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


class Approach22(Approach22Template):

  def __init__(self, **properties):
    self.init_components(**properties)
    self.file_media = None
    
  def returnhome_click(self, **event_args):
    open_form('Form1')

  def file_loader_change(self, file, **event_args):
    self.file_media = file
    Notification("File uploaded!", style="success").show()

  def button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    if self.file_media is None:
      Notification("Please upload a CSV first.", style="warning").show()
      return

    results = anvil.server.call(
      "analyze_dti_cognition",
      self.file_media
    )

    # Display HVLT table
    self.hvlt_repeating_panel.items = results["hvlt_table"]

    # Display VF table
    self.vf_repeating_panel.items = results["vf_table"]

    Notification("Analysis completed!", style="success").show()
