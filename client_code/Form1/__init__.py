from ._anvil_designer import Form1Template
from anvil import *
import anvil.server


class Form1(Form1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def file_loader_app1_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    lbl = Label(text=f"Uploaded: {file.name}")
    self.linear_panel_1.add_component(lbl)
    try:
      df_dict = anvil.server.call('process_uploaded_csv', file)
      open_form('Form2', df_data=df_dict)
    except Exception as e:
      alert(f"Server call failed: {e}")
      print(e)
    
    pass

  def button_app1_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('Form2')
    pass

  def button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    print(anvil.server.call('ping'))
    pass
