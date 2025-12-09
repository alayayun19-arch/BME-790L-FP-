from ._anvil_designer import Approach21Template
from anvil import *
import anvil.server

class Approach21(Approach21Template):

  def __init__(self, **properties):
    self.init_components(**properties)
    self.clinical_file = None
    self.analysis_result = None
    self._hide_all_results()

  # -------------------------
  def _hide_all_results(self):
    self.Demographic_characteristics.visible = False
    self.demographic_plot.visible = False
    self.label_plot_title.visible = False

  # -------------------------
  def file_loader_clinical_change(self, file, **event_args):
    if file is None:
      alert("Please upload a valid CSV.")
      return
    self.clinical_file = file
    alert("File uploaded successfully.")

  # START ANALYSIS only runs analysis → shows table
  def button_run_analysis_click(self, **event_args):
    if self.clinical_file is None:
      alert("Upload CSV first.")
      return

    self.button_run_analysis.enabled = False
    self.label_status.text = "Running..."
    self.label_status.foreground = "blue"
    self._hide_all_results()

    try:
      result = anvil.server.call("analyze_dm_vs_non_dm", self.clinical_file)
      self.analysis_result = result

      # ----- show table -----
      rows = result["rows"]
      n_dm = result["n_dm"]
      n_non = result["n_non"]

      self.repeating_panel_demographics.items = rows

      cols = self.Demographic_characteristics.columns
      cols[1]["title"] = f"DM_mean±SD (n={n_dm})"
      cols[2]["title"] = f"NonDM_mean±SD (n={n_non})"
      self.Demographic_characteristics.columns = cols
      self.Demographic_characteristics.visible = True

      self.label_status.text = "Analysis complete."
      self.label_status.foreground = "green"

    except Exception as e:
      alert(f"Error: {e}")
      self.label_status.text = "Analysis failed."
      self.label_status.foreground = "red"

    finally:
      self.button_run_analysis.enabled = True

  # PLOT 
  def button_plot_click(self, **event_args):
    if self.analysis_result is None:
      alert("Please run analysis first.")
      return

    dm_dict = self.analysis_result["dm_dict"]
    non_dict = self.analysis_result["non_dict"]

    plot_img = anvil.server.call("generate_plot", dm_dict, non_dict)

    self.demographic_plot.source = plot_img
    self.demographic_plot.visible = True
    self.label_plot_title.visible = True
    self.label_plot_title.text = "DM vs Non-DM: Bar Plot"


  # -------------------------
  # Home button
  # -------------------------
  def returnhome_click(self, **event_args):
    open_form('Form1')
