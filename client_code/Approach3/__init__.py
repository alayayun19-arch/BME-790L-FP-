from ._anvil_designer import Approach3Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
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

  def button_3_click(self, **event_args):
    """This method is called when the button is clicked"""
    """This method is called when 'Plot ECG Data' button is clicked"""
    if not self.uploaded_file:
      alert("Please upload a CSV file first!")
      return

    alert("Generating plots... This may take a few seconds.", title="Please wait")

    try:
      # Generate boxplots
      boxplot_img = anvil.server.call('generate_boxplots', self.uploaded_file)
      if boxplot_img:
        self.image_1.source = boxplot_img
        self.image_1.visible = True

      # Generate forest plot
      forest_img = anvil.server.call('generate_forest_plot', self.uploaded_file)
      if forest_img:
        self.image_2.source = forest_img
        self.image_2.visible = True

      alert("Plots generated successfully!")
    except Exception as e:
      alert(f"Error generating plots: {str(e)}")

  def file_loader_1_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    if not file:
      return

    self.uploaded_file = file
    alert(f"File uploaded: {file.name}")

    # Automatically load and show preview
    try:
      result = anvil.server.call('load_and_prepare_data', file)
      if result['status'] == 'success':
        alert(f"Data loaded successfully!\n"
              f"Total subjects: {result['total_subjects']}\n"
              f"Diabetic: {result['dm_count']}, Control: {result['control_count']}")
      else:
        alert(f"Error: {result.get('message', 'Unknown error')}")
    except Exception as e:
      alert(f"Error loading data: {str(e)}")

  def button_3_copy_click(self, **event_args):
    """This method is called when the button is clicked"""
    """This method is called when the button is clicked"""
    """This method is called when 'Plot ECG Data' button is clicked"""
    if not self.uploaded_file:
      alert("Please upload a CSV file first!")
      return

    alert("Generating plots... This may take a few seconds.", title="Please wait")

    try:
      # Generate boxplots
      boxplot_img = anvil.server.call('generate_bmi_correlations', self.uploaded_file)
      if boxplot_img:
        self.image_3.source = boxplot_img
        self.image_3.visible = True

      alert("Plots generated successfully!")
    except Exception as e:
      alert(f"Error generating plots: {str(e)}")

