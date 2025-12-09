# Approach1_2 client-side (synchronous call)
from ._anvil_designer import Approach1_2Template
from anvil import *
import anvil.server


class Approach1_2(Approach1_2Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    if hasattr(self, "status_label"):
      self.status_label.text = ""
    if hasattr(self, "trigger"):
      self.trigger.text = "trigger"

  def trigger_click(self, **event_args):
    """
    Synchronous server call (no call_async).
    Blocks the UI while the server function runs — OK for short runs.
    """
    uploaded_file = getattr(self, "file_loader_3", None) and self.file_loader_3.file
    if not uploaded_file:
      alert("Please upload a CSV file using file_loader_3 on this form.")
      return

    # UI: disable trigger and show status
    try:
      self.trigger.enabled = False
    except Exception:
      pass
    if hasattr(self, "status_label"):
      self.status_label.text = "Running analysis..."

    try:
      # Synchronous call to server function; replace name if your server fn differs
      resp = anvil.server.call("run_analysis_from_upload", uploaded_file, 10)

      # Handle server response
      if not isinstance(resp, dict) or not resp.get("ok", False):
        err = resp.get("error", "Unknown server error")
        tb = resp.get("traceback", "")
        if hasattr(self, "status_label"):
          self.status_label.text = "Server error: " + str(err)
        alert(f"Server error: {err}\nSee server logs for details.")
        print("Server traceback:\n", tb)
        return

      # Populate UI with returned medias and text
      if resp.get("report_img") is not None and hasattr(self, "ReportLL_output"):
        self.ReportLL_output.source = resp["report_img"]
      if resp.get("confusion_img") is not None and hasattr(self, "Confusion_Mat_output"):
        self.Confusion_Mat_output.source = resp["confusion_img"]
      if resp.get("pls_plot_img") is not None and hasattr(self, "PLS_plot_output"):
        self.PLS_plot_output.source = resp["pls_plot_img"]

      if hasattr(self, "PLS_output"):
        self.PLS_output.text = resp.get("pls_summary", "")
      if hasattr(self, "Linear_output"):
        self.Linear_output.text = resp.get("linear_summary", "")

      # show LL score in status_label if present
      if hasattr(self, "status_label"):
        llscore = resp.get("ll_score")
        if llscore is not None:
          self.status_label.text = f"Done. LL ROC AUC = {llscore:.4f}"
        else:
          self.status_label.text = "Done."

    except anvil.server.TimeoutError as e:
      # server-side took too long / timed out
      if hasattr(self, "status_label"):
        self.status_label.text = "Server timeout: the analysis took too long."
      alert("Server timeout: the analysis took too long. Consider using a Background Task for long runs.")
      print("TimeoutError:", e)
    except Exception as e:
      # generic client-side / server-side error
      tb = traceback.format_exc()
      if hasattr(self, "status_label"):
        self.status_label.text = "Error: " + str(e)
      alert("Error running analysis: " + str(e))
      print("Exception during synchronous call:\n", tb)
    finally:
      # restore trigger (even after open_form, this is safe)
      try:
        self.trigger.enabled = True
        self.trigger.text = "trigger"
      except Exception:
        pass

  def button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('Form1')
    pass
