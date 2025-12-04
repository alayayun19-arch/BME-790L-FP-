from ._anvil_designer import Approach21Template
from anvil import *
import anvil.server


class Approach21(Approach21Template):

  def __init__(self, **properties):
    self.init_components(**properties)
    # Store uploaded CSV file
    self.clinical_file = None

  def file_loader_clinical_change(self, file, **event_args):
    """
    Triggered when user selects a CSV file.
    """
    if file is None:
      alert("No file selected. Please upload a CSV file.")
      return

    self.clinical_file = file
    alert("File uploaded successfully.")

  def button_run_analysis_click(self, **event_args):
    """
    Triggered when user clicks 'Start analysis'.
    Calls the server, then displays all results
    in the Demographic_characteristics DataGrid.
    """
    if self.clinical_file is None:
      alert("Please upload the clinical CSV file first.")
      return
  
    # ---- BEFORE calling the server: show "running" status ----
    self.button_run_analysis.enabled = False
    self.label_status.text = "Running analysis, please wait..."
    self.label_status.foreground = "blue"   # optional: show as blue text
  
    try:
      # Call server: get rows + sample sizes
      result = anvil.server.call(
        'analyze_dm_vs_non_dm',
        self.clinical_file
      )
  
      rows = result["rows"]
      n_dm = result["n_dm"]
      n_non = result["n_non"]
  
      # Bind rows to the DataGrid
      self.Demographic_characteristics.items = rows
  
      # Update column headers to show group sample sizes
      cols = self.Demographic_characteristics.columns
      cols[1].title = f"DM_mean±SD (n={n_dm})"
      cols[2].title = f"NonDM_mean±SD (n={n_non})"
      cols[3].title = "p_value"
  
      # ---- AFTER success: update status ----
      self.label_status.text = "Analysis completed successfully."
  
    except Exception as e:
      # ---- On error: show error status ----
      self.label_status.text = "Analysis failed. See error message."
      alert(f"Error during analysis: {e}")
  
    finally:
      # ---- Always re-enable button ----
      self.button_run_analysis.enabled = True

  def returnhome_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('Form1')
    pass
