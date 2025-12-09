import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.media
import pandas as pd
import numpy as np
from io import BytesIO
import traceback
import warnings

# plotting backend for server
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# sklearn
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score

# ---- helper functions adapted from your script ----

def read_input_from_media(file_media):
  raw = file_media.get_bytes()
  df = pd.read_csv(BytesIO(raw), encoding="ISO-8859-1")
  return df

def find_output_column(df):
  # If you have a known output column name, replace this logic.
  # Try common names first; otherwise use second column (index 1).
  for candidate in ("Outcome", "outcome", "target", "label", "y", "Y"):
    if candidate in df.columns:
      return df[candidate]
    # fallback: use second column if exists
  if df.shape[1] >= 2:
    return df.iloc[:, 1]
    # else error
  raise ValueError("Cannot find an outcome column. Add a column named Outcome/target or ensure CSV has >=2 columns.")

def df_to_features_and_output(df):
  # following your filled_imp behaviour: use columns from index 2 onward as features
  input_filled = df.iloc[:, 2:].copy()
  output_raw = find_output_column(df)
  return input_filled.reset_index(drop=True), output_raw.reset_index(drop=True)

def PLSReg(X_train,X_test,Y_train,Y_test,n_com):
  pls_model = PLSRegression(n_components = n_com)
  pls_model.fit(X_train,Y_train)
  score = pls_model.score(X_test,Y_test)
  return pls_model,score

def FindB_PLSReg_plot(X_train,X_test,Y_train,Y_test,max_n,string):
  score_list = []
  for i in range(1, max_n+1):
    _,score = PLSReg(X_train,X_test,Y_train,Y_test,i)
    score_list.append(score)
  return score_list

def PLS_CV(pls_model,X_test,Y_test,CV):
  cv_score = cross_val_score(pls_model,X_test,Y_test,cv = CV)
  return np.mean(cv_score), cv_score

def LogReg(X_train,X_test,Y_train,Y_test,max_iter,C=1.0):
  Log_Model = LogisticRegression(penalty = 'l1',solver='saga',C=C,max_iter=max_iter,random_state=0)
  with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category = UserWarning)
    Log_Model.fit(X_train,Y_train)
    Y_pred = Log_Model.predict(X_test)
    Y_proba = Log_Model.predict_proba(X_test)[:, 1]
    score = roc_auc_score(Y_test, Y_proba)
    return score, Y_test, Y_pred

def LL_printing_plot(Y_test, Y_pred):
  cm = confusion_matrix(Y_test, Y_pred)
  report_dict = classification_report(Y_test, Y_pred, output_dict = True)
  report_df = pd.DataFrame(report_dict).transpose()
  # Confusion matrix figure
  fig1, ax1 = plt.subplots(figsize=(5,4))
  labels = np.unique(Y_test)
  sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels, ax=ax1)
  ax1.set_xlabel('Predicted Label')
  ax1.set_ylabel('True Label')
  ax1.set_title('Confusion Matrix')
  buf1 = BytesIO()
  fig1.tight_layout()
  fig1.savefig(buf1, format='png')
  plt.close(fig1)
  buf1.seek(0)

  # Classification report figure (drop support column if present)
  report_plot = report_df.copy()
  if 'support' in report_plot.columns:
    report_plot = report_plot.drop(columns=['support'])
    # remove last rows like accuracy/weighted avg if too many; but we'll plot all rows except "accuracy" row if present
  try:
    to_plot = report_plot.iloc[:-3, :]  # as in your script
  except Exception:
    to_plot = report_plot
  fig2, ax2 = plt.subplots(figsize=(6, max(2, 0.4 * to_plot.shape[0])))
  sns.heatmap(to_plot, annot=True, cmap='viridis', fmt=".2f", ax=ax2)
  ax2.set_title('Classification Report Metrics (per class)')
  buf2 = BytesIO()
  fig2.tight_layout()
  fig2.savefig(buf2, format='png')
  plt.close(fig2)
  buf2.seek(0)
  return buf2, buf1  # report plot (metrics), confusion matrix

# ---- Main server function that runs the pipeline ----
@anvil.server.callable
def run_analysis_from_upload(file_media, max_pls_components=10):
  """
    Runs the adapted pipeline on the uploaded CSV (file_media).
    Returns dict with medias and numeric scores.
    """
  try:
    if file_media is None:
      return {"ok": False, "error": "No file uploaded."}

    df = read_input_from_media(file_media)
    # derive input features and output
    input_filled, output_raw = df_to_features_and_output(df)

    # Train/test split (your original choices)
    input_train_lin, input_test_lin, output_train_lin, output_test_lin = train_test_split(
      input_filled, output_raw, random_state=37, test_size=0.2
    )

    # Scaling and feature splitting (guard for columns count)
    num_cols_count = min(49, input_filled.shape[1])
    X_num = input_filled.iloc[:, :num_cols_count]
    X_cate = input_filled.drop(columns=input_filled.columns[:num_cols_count], errors='ignore')

    X_scaled_num = StandardScaler().fit_transform(X_num)
    X_scaled_df_num = pd.DataFrame(X_scaled_num, index=X_num.index, columns=X_num.columns)
    X_scaled = pd.concat([X_scaled_df_num, X_cate.reset_index(drop=True)], axis=1).fillna(0)

    # Train/test on scaled
    in_train_scaled, in_test_scaled, out_train_scaled, out_test_scaled = train_test_split(
      X_scaled, output_raw, random_state=37, test_size=0.2
    )


    # PLS: find scores across components and keep plot & list
    report_buf_pls, score_list = FindB_PLSReg_plot(in_train_scaled, in_test_scaled, out_train_scaled, out_test_scaled, max_pls_components, "Scaled_OHT_Full")
    # pick a component (you used 7 previously) - choose best from scores if possible
    try:
      O_component = int(np.argmax(score_list) + 1)
    except Exception:
      O_component = min(7, max_pls_components)

    pls_model, pls_score = PLSReg(in_train_scaled, in_test_scaled, out_train_scaled, out_test_scaled, n_com=O_component)
    cv_mean, cv_scores = PLS_CV(pls_model, X_scaled, output_raw, CV=5)

    # Lasso-Logistic: use 40% test as in your script for LL portion
    in_train_scaled2,in_test_scaled2, out_train_scaled2, out_test_scaled2 = train_test_split(X_scaled, output_raw, random_state=37, test_size=0.4)
    LL_score, LL_test, LL_pred = LogReg(in_train_scaled2, in_test_scaled2, out_train_scaled2, out_test_scaled2, max_iter=5000, C=1.0)

    # Build report & confusion plots from LL output
    report_buf, conf_buf = LL_printing_plot(LL_test, LL_pred)

    # convert buffers to anvil.media
    report_media = anvil.media.from_bytes(report_buf.getvalue(), "image/png", name="ReportLL.png")
    confusion_media = anvil.media.from_bytes(conf_buf.getvalue(), "image/png", name="Confusion_Matrix.png")

    # Prepare numeric summary strings
    pls_summary = f"PLS R2 (chosen n={O_component}): {pls_score:.4f} (CV mean: {cv_mean:.4f})"

    return {
      "ok": True,
      "report_img": report_media,
      "confusion_img": confusion_media,
      "pls_plot_img": pls_plot_media,
      "pls_summary": pls_summary,
      "ll_score": float(LL_score)
    }

  except Exception as e:
    tb = traceback.format_exc()
    return {"ok": False, "error": str(e), "traceback": tb}

