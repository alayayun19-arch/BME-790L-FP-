from ._anvil_designer import Approach21Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


class Approach21(Approach21Template):

  def __init__(self, **properties):
    # Set up form and store uploaded clinical CSV
    self.init_components(**properties)
    self.clinical_file = None

    #---------- Initial state: Hide all result-related components ----------
    # whole demographic chart
    self.Demographic_characteristics.visible = False

    # GM 
    self.label_gm_title.visible = False
    self.datagrid_gm.visible = False
    self.image_gm.visible = False

    # WM 
    self.label_wm_title.visible = False
    self.datagrid_wm.visible = False
    self.image_wm.visible = False

    # CSF 
    self.label_csf_title.visible = False
    self.datagrid_csf.visible = False
    self.image_csf.visible = False

    # WMH 
    self.label_wmh_title.visible = False
    self.datagrid_wmh.visible = False
    self.image_wmh.visible = False

  # ---------- File loader: upload CSV ----------
  def file_loader_clinical_change(self, file, **event_args):
    """
    Called when the user selects a CSV file.
    """
    if file is None:
      alert("No file selected. Please upload a CSV file.")
      return

    self.clinical_file = file
    alert("File uploaded successfully.")

  # ---------- Run analysis ----------
  def button_run_analysis_click(self, **event_args):
    """
    Called when the user clicks 'Start analysis'.
    """
    if self.clinical_file is None:
      alert("Please upload the clinical CSV file first.")
      return

    # Update status label and disable the button during analysis
    self.button_run_analysis.enabled = False
    self.label_status.text = "Running analysis, please wait..."
    self.label_status.foreground = "blue"

    self.Demographic_characteristics.visible = False
    self.label_gm_title.visible = False
    self.datagrid_gm.visible = False
    self.image_gm.visible = False
    self.label_wm_title.visible = False
    self.datagrid_wm.visible = False
    self.image_wm.visible = False
    self.label_csf_title.visible = False
    self.datagrid_csf.visible = False
    self.image_csf.visible = False
    self.label_wmh_title.visible = False
    self.datagrid_wmh.visible = False
    self.image_wmh.visible = False

    try:
      # 1) Call the server
      result = anvil.server.call(
        'analyze_dm_vs_non_dm',
        self.clinical_file
      )

      # ------------------------------
      # 2) Demographic/global 
      # ------------------------------
      rows = result["rows"]
      n_dm = result["n_dm"]
      n_non = result["n_non"]

      self.repeating_panel_demographics.items = rows

      cols = self.Demographic_characteristics.columns
      cols[1]["title"] = f"DM_mean±SD (n={n_dm})"
      cols[2]["title"] = f"NonDM_mean±SD (n={n_non})"
      cols[3]["title"] = "p_value"
      self.Demographic_characteristics.columns = cols

      # 分析完再显示这块
      self.Demographic_characteristics.visible = True

      # ------------------------------
      # 3) GM / WM / CSF / WMH 表格
      # ------------------------------
      gm_rows = result.get("gm_rows", [])
      wm_rows = result.get("wm_rows", [])
      csf_rows = result.get("csf_rows", [])
      wmh_rows = result.get("wmh_rows", [])

      self.repeating_panel_gm.items = gm_rows
      self.repeating_panel_wm.items = wm_rows
      self.repeating_panel_csf.items = csf_rows
      self.repeating_panel_wmh.items = wmh_rows
      
      if gm_rows:
        self.label_gm_title.visible = True
        self.datagrid_gm.visible = True
      if wm_rows:
        self.label_wm_title.visible = True
        self.datagrid_wm.visible = True
      if csf_rows:
        self.label_csf_title.visible = True
        self.datagrid_csf.visible = True
      if wmh_rows:
        self.label_wmh_title.visible = True
        self.datagrid_wmh.visible = True

      # ------------------------------
      # 4) GM / WM / CSF / WMH 
      # ------------------------------
      gm_plot = result.get("gm_plot", None)
      if gm_plot is not None:
        self.image_gm.source = gm_plot
        self.image_gm.visible = True

      wm_plot = result.get("wm_plot", None)
      if wm_plot is not None:
        self.image_wm.source = wm_plot
        self.image_wm.visible = True

      csf_plot = result.get("csf_plot", None)
      if csf_plot is not None:
        self.image_csf.source = csf_plot
        self.image_csf.visible = True

      wmh_plot = result.get("wmh_plot", None)
      if wmh_plot is not None:
        self.image_wmh.source = wmh_plot
        self.image_wmh.visible = True

      # ------------------------------
      # 5) Status
      # ------------------------------
      self.label_status.text = (
        f"Analysis completed successfully. "
        f"Metrics (demographics/global) = {len(rows)}"
      )
      self.label_status.foreground = "green"

    except Exception as e:
      self.label_status.text = "Analysis failed. See error message."
      self.label_status.foreground = "red"
      alert(f"Error during analysis: {e}")

    finally:
      self.button_run_analysis.enabled = True

  def returnhome_click(self, **event_args):
    """Called when the 'Home' button is clicked."""
    open_form('Form1')
