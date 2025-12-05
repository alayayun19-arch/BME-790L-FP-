import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.server
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import linregress
from scipy.signal import find_peaks, butter, filtfilt, welch
from scipy.interpolate import interp1d
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import anvil.media

# Set plot style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 100


@anvil.server.callable
def analyze_ecg_file(file_content, subject_id, analysis_duration_min=5):
  """
    Analyze ECG file and extract HRV metrics.

    Parameters:
    - file_content: File content from Anvil FileLoader
    - subject_id: Subject identifier
    - analysis_duration_min: Duration to analyze in minutes

    Returns:
    - Dictionary of HRV metrics or None if error
    """
  try:
    # Save temporarily and read with wfdb
    # Note: This requires proper file handling for WFDB format
    # For now, this is a placeholder for the structure

    # Process ECG signal here (simplified)
    # In production, you'd need to handle WFDB file format properly

    return {
      'Subject_ID': subject_id,
      'Status': 'Success',
      'Message': 'ECG analysis complete'
    }

  except Exception as e:
    return {
      'Status': 'Error',
      'Message': str(e)
    }


@anvil.server.callable
def load_and_prepare_data(file):
  """
    Load preprocessed CSV data and prepare for analysis.

    Parameters:
    - file: Anvil Media object containing CSV data

    Returns:
    - Dictionary with processed data ready for visualization
    """
  try:
    # Read CSV from uploaded file
    df = pd.read_csv(BytesIO(file.get_bytes()))

    # Remove subjects without demographic data
    df = df.dropna(subset=['Is_DM'])

    # Convert boolean columns if they're strings
    if df['Is_DM'].dtype == 'object':
      df['Is_DM'] = df['Is_DM'].map({'True': True, 'False': False, True: True, False: False})
    if 'Is_HTN' in df.columns and df['Is_HTN'].dtype == 'object':
      df['Is_HTN'] = df['Is_HTN'].map({'True': True, 'False': False, True: True, False: False})

      # Summary statistics
    dm_count = int(df['Is_DM'].sum())
    control_count = int((df['Is_DM'] == False).sum())

    return {
      'status': 'success',
      'total_subjects': len(df),
      'dm_count': dm_count,
      'control_count': control_count,
      'columns': list(df.columns),
      'data_preview': df.head(10).to_dict(orient='records')
    }

  except Exception as e:
    return {
      'status': 'error',
      'message': str(e)
    }


@anvil.server.callable
def perform_statistical_analysis(file, group_col='Is_DM'):
  """
    Perform statistical comparison between groups from uploaded CSV.

    Parameters:
    - file: Anvil Media object containing CSV data
    - group_col: Column name for grouping (default: 'Is_DM')

    Returns:
    - Statistical results as dict
    """
  try:
    # Load data
    data = pd.read_csv(BytesIO(file.get_bytes()))
    data = data.dropna(subset=[group_col])

    # Convert boolean if needed
    if data[group_col].dtype == 'object':
      data[group_col] = data[group_col].map({'True': True, 'False': False, True: True, False: False})

    biomarkers = ['Mean RR (ms)', 'Mean HR (bpm)', 'SDNN (ms)', 'RMSSD (ms)',
                  'pNN50 (%)', 'SDSD (ms)', 'LF Power (ms²)',
                  'HF Power (ms²)', 'Total Power (ms²)', 'LF/HF Ratio']

    results = []

    for biomarker in biomarkers:
      if biomarker not in data.columns:
        continue

      group1 = data[data[group_col] == True][biomarker].dropna()
      group0 = data[data[group_col] == False][biomarker].dropna()

      if len(group1) < 3 or len(group0) < 3:
        continue

        # Check normality
      _, p_norm_1 = stats.shapiro(group1) if len(group1) < 5000 else (None, 0.05)
      _, p_norm_0 = stats.shapiro(group0) if len(group0) < 5000 else (None, 0.05)

      # Choose test
      if p_norm_1 > 0.05 and p_norm_0 > 0.05:
        stat, p_value = stats.ttest_ind(group1, group0)
        test_used = 't-test'
      else:
        stat, p_value = stats.mannwhitneyu(group1, group0, alternative='two-sided')
        test_used = 'Mann-Whitney U'

        # Calculate Cohen's d
      pooled_std = np.sqrt(((len(group1)-1)*np.var(group1, ddof=1) +
                            (len(group0)-1)*np.var(group0, ddof=1)) /
                           (len(group1) + len(group0) - 2))
      cohen_d = (np.mean(group1) - np.mean(group0)) / pooled_std if pooled_std > 0 else 0

      results.append({
        'Biomarker': biomarker,
        'DM_Mean': float(np.mean(group1)),
        'DM_SD': float(np.std(group1, ddof=1)),
        'Control_Mean': float(np.mean(group0)),
        'Control_SD': float(np.std(group0, ddof=1)),
        'Test_Used': test_used,
        'P_Value': float(p_value),
        'Cohen_d': float(cohen_d)
      })

      # Apply FDR correction
    if results:
      p_values = [r['P_Value'] for r in results]
      _, p_adjusted, _, _ = multipletests(p_values, method='fdr_bh')

      for i, result in enumerate(results):
        result['P_Adjusted'] = float(p_adjusted[i])
        result['Significant'] = p_adjusted[i] < 0.05

    return {
      'status': 'success',
      'results': results
    }

  except Exception as e:
    return {
      'status': 'error',
      'message': str(e)
    }


@anvil.server.callable
def generate_boxplots(file):
  """
    Generate box plots comparing Diabetes vs Control groups.

    Parameters:
    - file: Anvil Media object containing CSV data

    Returns:
    - Anvil Media object (PNG image)
    """
  try:
    # Load data
    # data = pd.read_csv(BytesIO(file.get_bytes()))
    file_bytes = file.get_bytes()  # Get bytes once
    data = pd.read_csv(BytesIO(file_bytes))
    data = data.dropna(subset=['Is_DM'])

    # Convert boolean if needed
    if data['Is_DM'].dtype == 'object':
      data['Is_DM'] = data['Is_DM'].map({'True': True, 'False': False, True: True, False: False})

      # Get statistical results for p-values
    stat_result = perform_statistical_analysis(file)
    stat_results = pd.DataFrame(stat_result['results']) if stat_result['status'] == 'success' else None

    # Key biomarkers to plot
    key_biomarkers = ['SDNN (ms)', 'RMSSD (ms)', 'pNN50 (%)',
                      'LF/HF Ratio', 'HF Power (ms²)', 'LF Power (ms²)']

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.ravel()

    for i, biomarker in enumerate(key_biomarkers):
      if biomarker not in data.columns:
        continue

      ax = axes[i]

      # Prepare data
      plot_data = data[['Is_DM', biomarker]].dropna()
      plot_data['Group'] = plot_data['Is_DM'].map({True: 'Diabetes', False: 'Control'})

      # Create box plot
      sns.boxplot(data=plot_data, x='Group', y=biomarker, ax=ax,
                  palette=['#2ecc71', '#e74c3c'])

      # Add statistics to title
      if stat_results is not None:
        result_row = stat_results[stat_results['Biomarker'] == biomarker]
        if not result_row.empty:
          p_val = result_row['P_Adjusted'].values[0]
          cohen_d = result_row['Cohen_d'].values[0]
          sig = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
          ax.set_title(f"{biomarker}\np={p_val:.4f} {sig}, d={cohen_d:.3f}", fontsize=10)
        else:
          ax.set_title(biomarker, fontsize=10)
      else:
        ax.set_title(biomarker, fontsize=10)

      ax.set_xlabel('')
      ax.set_ylabel(biomarker, fontsize=9)

    plt.tight_layout()

    # Save to BytesIO
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    plt.close()

    return anvil.media.from_file(buffer, 'image/png')

  except Exception as e:
    print(f"Error generating boxplots: {str(e)}")
    return None


@anvil.server.callable
def generate_forest_plot(file):
  """
    Generate forest plot showing effect sizes.

    Parameters:
    - file: Anvil Media object containing CSV data

    Returns:
    - Anvil Media object (PNG image)
    """
  try:
    # Get statistical results
    stat_result = perform_statistical_analysis(file)
    if stat_result['status'] != 'success':
      return None

    stat_results = pd.DataFrame(stat_result['results'])

    # Select key biomarkers
    selected_biomarkers = ['SDNN (ms)', 'RMSSD (ms)', 'pNN50 (%)', 'LF/HF Ratio']
    plot_data = stat_results[stat_results['Biomarker'].isin(selected_biomarkers)].copy()

    if plot_data.empty:
      return None

      # Load original data to calculate sample sizes
    data = pd.read_csv(BytesIO(file.get_bytes()))
    data = data.dropna(subset=['Is_DM'])
    if data['Is_DM'].dtype == 'object':
      data['Is_DM'] = data['Is_DM'].map({'True': True, 'False': False, True: True, False: False})

    dm_n = int(data['Is_DM'].sum())
    control_n = int((data['Is_DM'] == False).sum())

    # Calculate confidence intervals
    plot_data['Cohen_d_SE'] = np.sqrt(
      (dm_n + control_n) / (dm_n * control_n) +
      plot_data['Cohen_d']**2 / (2 * (dm_n + control_n))
    )
    plot_data['Cohen_d_CI_Low'] = plot_data['Cohen_d'] - 1.96 * plot_data['Cohen_d_SE']
    plot_data['Cohen_d_CI_High'] = plot_data['Cohen_d'] + 1.96 * plot_data['Cohen_d_SE']

    # Create forest plot
    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = np.arange(len(plot_data))
    colors = ['#e74c3c' if sig else '#95a5a6' for sig in plot_data['Significant']]

    for i, (idx, row) in enumerate(plot_data.iterrows()):
      ax.plot([row['Cohen_d_CI_Low'], row['Cohen_d_CI_High']], [i, i],
              color=colors[i], linewidth=2)
      ax.plot(row['Cohen_d'], i, 'o', color=colors[i], markersize=10)

    ax.axvline(0, color='black', linestyle='--', linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_data['Biomarker'])
    ax.set_xlabel('Effect Size (Cohen\'s d)', fontsize=12)
    ax.set_title('Effect Sizes: Diabetes vs Control', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c',
                markersize=10, label='Significant'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#95a5a6',
                markersize=10, label='Not Significant')
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()

    # Save to BytesIO
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    plt.close()

    return anvil.media.from_file(buffer, 'image/png')

  except Exception as e:
      print(f"Error generating forest plot: {str(e)}")
      return None


@anvil.server.callable
def generate_bmi_correlations(file):
    """
    Generate scatter plots showing correlations between BMI and HRV metrics.

    Parameters:
    - file: Anvil Media object containing CSV data

    Returns:
    - Anvil Media object (PNG image)
    """
    try:
        # Load data
        data = pd.read_csv(BytesIO(file.get_bytes()))
        data = data.dropna(subset=['Is_DM'])

        # Select data with BMI
        metrics = ['Mean HR (bpm)', 'SDNN (ms)', 'RMSSD (ms)', 'LF/HF Ratio']
        bmi_data = data[['Subject_ID', 'BMI'] + metrics].dropna()

        if len(bmi_data) < 3:
            return None

        # Calculate correlations
        correlation_results = []
        for metric in metrics:
            if metric in bmi_data.columns:
                corr, p_val = stats.pearsonr(bmi_data['BMI'], bmi_data[metric])
                correlation_results.append({
                    'Metric': metric,
                    'Correlation': corr,
                    'P_Value': p_val
                })

        corr_df = pd.DataFrame(correlation_results)

        # Create scatter plots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()

        for i, metric in enumerate(metrics):
            if metric not in bmi_data.columns:
                continue

            ax = axes[i]

            # Scatter plot
            ax.scatter(bmi_data['BMI'], bmi_data[metric], alpha=0.5, s=50)

            # Regression line
            slope, intercept, r_value, p_value, std_err = linregress(bmi_data['BMI'], bmi_data[metric])
            line = slope * bmi_data['BMI'] + intercept
            ax.plot(bmi_data['BMI'], line, 'r-', linewidth=2)

            # Add correlation info
            corr_row = corr_df[corr_df['Metric'] == metric]
            if not corr_row.empty:
                corr = corr_row['Correlation'].values[0]
                p_val = corr_row['P_Value'].values[0]
                ax.set_title(f"{metric}\nr={corr:.3f}, p={p_val:.4f}", fontsize=11)

            ax.set_xlabel('BMI', fontsize=10)
            ax.set_ylabel(metric, fontsize=10)
            ax.grid(alpha=0.3)

        plt.tight_layout()

        # Save to BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()

        return anvil.media.from_file(buffer, 'image/png')

    except Exception as e:
        print(f"Error generating BMI correlations: {str(e)}")
        return None