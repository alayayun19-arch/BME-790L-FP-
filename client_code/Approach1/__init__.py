from ._anvil_designer import Approach1Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.media
import anvil.users
from .RowTemplate import RowTemplate
from .FeatureRowTemplate import FeatureRowTemplate

class Approach1(Approach1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    # init state

  def button_load_click(self, **event_args):
    uploaded_file = self.file_loader_app1.file
    max_rows = 20   # change as needed
    
    if not uploaded_file:
      print("No file uploaded!")
      return

    resp = anvil.server.call('process_csv_file', uploaded_file)
    records = resp.get('records', [])
    columns = resp.get('columns', [])
    print("Got", len(records), "records and", len(columns), "columns")

    # inject columns into each record so the template always has access
    for r in records:
      r["_columns"] = columns

    self.repeating_panel_1.item_template = RowTemplate
    self.repeating_panel_1.items = records[:max_rows]
    # still OK to set item_template_args if you want, but not required now
    # self.repeating_panel_1.item_template_args = {"columns": columns}
  
    
  def independency_check_click(self, **event_args):
    uploaded_file = self.file_loader_2.file
    if not uploaded_file:
      alert("Please upload a CSV first.")
      return

      # UI feedback
    self.independency_check.enabled = False
    self.independence.text = "Running independence check..."

    try:
      resp = anvil.server.call('independency_check', uploaded_file, 200)
      if not resp.get("ok", False):
        self.independence.text = "Server error: " + resp.get("error", "Unknown")
        print(resp.get("traceback", ""))
        return

      result = resp["result"]
      # Format a short summary for the label
      summary = f"{result.get('conclusion')}\nPairs: {result.get('n_pairs')}\n"
      d1 = result.get('dcor_with_ohe', {})
      summary += f"dCor (with OHE): stat={d1.get('stat'):.4f}, p={d1.get('pval'):.4g}\n"
      d2 = result.get('dcor_numeric_only', {})
      if d2.get('stat') is not None:
        summary += f"dCor (numeric): stat={d2.get('stat'):.4f}, p={d2.get('pval'):.4g}\n"
      self.independence.text = summary

    except Exception as e:
      self.independence.text = "Client error: " + str(e)
    finally:
      self.independency_check.enabled = True

  