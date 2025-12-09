# Approach1_2 client-side code
from ._anvil_designer import Approach1_2Template
from anvil import *
import anvil.server

class Approach1_2(Approach1_2Template):
  def __init__(self, **properties):
    # Set up form (designer-generated components are available after init_components)
    self.init_components(**properties)
    # initial UI state
    if hasattr(self, "trigger"):
      self.trigger.text = "trigger"
    if hasattr(self, "status_label"):
      self.status_label.text = ""

  def trigger_click(self, **event_args):
    """
    Called when the trigger button is clicked on Approach1_2.
    Reads file_loader_3.file and calls server async.
    """
    # get uploaded file from this form's FileLoader
    uploaded_file = getattr(self, "file_loader_3", None) and self.file_loader_3.file
    if not uploaded_file:
      alert("Please upload a CSV file using file_loader_3 on this form.")
      return

    # UI: disable button and show running text
    try:
      self.trigger.enabled = False
    except Exception:
      pass
    if hasattr(self, "status_label"):
      self.status_label.text = "Running analysis..."

    # async server call; adjust max_pls_components param if you like
    fut = anvil.server.call_async("run_analysis_from_upload", uploaded_file, 10)
    fut.add_done_callback(self._analysis_done)

  def _analysis_done(self, fut):
    """Callback invoked when the server-side analysis finishes (or errors)."""
    try:
      resp = fut.result()
    except Exception as e:
      # network / client-side error
      if hasattr(self, "status_label"):
        self.status_label.text = "Client error calling server: " + str(e)
      alert("Client error: " + str(e))
      try:
        self.trigger.enabled = True
        self.trigger.text = "trigger"
      except Exception:
        pass
      return

    # handle server response
    if not isinstance(resp, dict) or not resp.get("ok", False):
      # server indicated error
      err = resp.get("error", "Unknown server error")
      tb = resp.get("traceback", "")
      if hasattr(self, "status_label"):
        self.status_label.text = "Server error: " + str(err)
      alert(f"Server error: {err}\nSee server logs for details.")
      print("Server traceback:\n", tb)
      try:
        self.trigger.enabled = True
        self.trigger.text = "trigger"
      except Exception:
        pass
      return

    # OK — place returned images and text into this same form's components
    try:
      # Images (these must be Image components on this form)
      if resp.get("report_img") is not None and hasattr(self, "ReportLL_output"):
        self.ReportLL_output.source = resp["report_img"]
      if resp.get("confusion_img") is not None and hasattr(self, "Confusion_Mat_output"):
        self.Confusion_Mat_output.source = resp["confusion_img"]
      # optional PLS plot image
      if resp.get("pls_plot_img") is not None and hasattr(self, "PLS_plot_output"):
        self.PLS_plot_output.source = resp["pls_plot_img"]

      # Labels for numeric summaries
      if hasattr(self, "PLS_output"):
        self.PLS_output.text = resp.get("pls_summary", "")
      if hasattr(self, "Linear_output"):
        self.Linear_output.text = resp.get("linear_summary", "")

      # status / LL score
      if hasattr(self, "status_label"):
        # show LL ROC AUC optionally
        llscore = resp.get("ll_score")
        if llscore is not None:
          self.status_label.text = f"Done. LL ROC AUC = {llscore:.4f}"
        else:
          self.status_label.text = "Done."

    except Exception as e:
      # unexpectedly failed to set UI components
      if hasattr(self, "status_label"):
        self.status_label.text = "Error updating UI: " + str(e)
      print("UI update exception:", e)
      alert("Error updating UI with results: " + str(e))
    finally:
      # re-enable trigger
      try:
        self.trigger.enabled = True
        self.trigger.text = "trigger"
      except Exception:
        pass
