from ._anvil_designer import Form1Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.media
import anvil.users

class Form1(Form1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.

  def button_app1_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form("Approach1")
    pass
    
  def approach2_part1_click(self, **event_args):
     """This method is called when the button is clicked"""
     open_form('Approach21')
     pass
   
  def button_app3_click(self, **event_args):
     """This method is called when the button is clicked"""
     open_form('Approach3')
     pass
  def button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    print(anvil.server.call('ping'))
    pass

  def approach2_part2_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('Approach22')
    pass
