from ._anvil_designer import Approach22Template
from anvil import *
import anvil.server


class Approach22(Approach22Template):

  def __init__(self, **properties):
    self.init_components(**properties)
    self.file_media = None

    # Hide everything on start
    self._hide_all_results()

  # ---------------------------------------------
  # Hide both DataGrids (including their headers)
  # ---------------------------------------------
  def _hide_all_results(self):
    # HVLT section
    self.hvlt_datagrid.visible = False
    self.hvlt_repeating_panel.visible = False

    # VF section
    self.vf_datagrid.visible = False
    self.vf_repeating_panel.visible = False

  # ---------------------------------------------
  # File upload
  # ---------------------------------------------
  def file_loader_change(self, file, **event_args):
    if file is None:
      alert("Please upload a valid CSV file.")
      return

    self.file_media = file
    alert("File uploaded successfully!")

    # Hide previous results whenever a new file is uploaded
    self._hide_all_results()

  # ---------------------------------------------
  # Run analysis
  # ---------------------------------------------
  def run_btn_click(self, **event_args):
    if self.file_media is None:
      alert("Upload a CSV first.")
      return

    self.run_btn.enabled = False
    self.label_status.text = "Running..."
    self.label_status.foreground = "blue"

    # Hide old results
    self._hide_all_results()

    try:
      results = anvil.server.call(
        "analyze_dti_cognition",
        self.file_media
      )

      # Populate tables
      self.hvlt_repeating_panel.items = results["hvlt_table"]
      self.vf_repeating_panel.items = results["vf_table"]

      # Make DataGrids visible
      self.hvlt_datagrid.visible = True
      self.hvlt_repeating_panel.visible = True

      self.vf_datagrid.visible = True
      self.vf_repeating_panel.visible = True

      self.label_status.text = "Analysis complete!"
      self.label_status.foreground = "green"

    except Exception as e:
      alert(f"Error during analysis: {e}")
      self.label_status.text = "Analysis failed."
      self.label_status.foreground = "red"

    finally:
      self.run_btn.enabled = True

  # Return home
  def returnhome_click(self, **event_args):
    open_form("Form1")
    pass
