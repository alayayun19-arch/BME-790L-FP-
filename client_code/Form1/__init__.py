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
    self.store_mode = "dataframe_json"  # Changes made by Shiao Xu Dec 4
    # Any code you write here will run before the form opens.

  def file_loader_app1_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    '''lbl = Label(text=f"Uploaded: {file.name}")
    self.linear_panel_1.add_component(lbl)
    try:
      result = anvil.server.call('save_uploaded_file', file)
      anvil.server.call('store_df_in_session', result)
    except Exception as e:
      alert(f"Server call failed: {e}")
      print(e)'''
    pass

  def button_app1_click(self, **event_args):
    """This method is called when the button is clicked"""
    media = self.file_loader_app1.file
    if not media:
      anvil.alert("Please choose a CSV file first.")
      return
      # optionally show a small message / spinner
    anvil.alert("Uploading and processing... (this may take a few seconds)", title="Please wait")

    try:
      result = anvil.server.call('process_csv_file', media, self.store_mode)
    except Exception as e:
      anvil.alert("Error processing file on server:\n" + str(e))
      return

    '''if result.get("status") == "ok":
      anvil.alert(f"Saved OK (storage={result.get('storage')}). Row id: {result.get('row_id')}")
    else:
      anvil.alert("Server returned error: " + str(result))'''

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
