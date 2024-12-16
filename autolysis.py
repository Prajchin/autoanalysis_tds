import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import subprocess
from tabulate import tabulate
import json
import chardet
# Verify environment variable for AI Proxy Token
if "AIPROXY_TOKEN" not in os.environ:
    print("Error: AIPROXY_TOKEN environment variable not set.")
    sys.exit(1)

AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]

# Check command-line arguments
if len(sys.argv) != 2:
    print("Usage: python autolysis.py <dataset.csv>")
    sys.exit(1)

filename = sys.argv[1]
if not os.path.isfile(filename):
    print(f"Error: File '{filename}' not found.")
    sys.exit(1)
dataset_name = os.path.splitext(os.path.basename(filename))[0]
output_folder = os.path.join(os.getcwd(), dataset_name)
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Load dataset
def detect_encoding(file_path):
    """
    Detects the file encoding using chardet.
    """
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
        return result['encoding']
encoding=detect_encoding(filename)
data = pd.read_csv(filename,encoding=encoding,encoding_errors="replace")


# Summary statistics and data inspection
def summarize_data(df):
    summary = {
        "Shape": df.shape,
        "Columns": df.dtypes.to_dict(),
        "Missing Values": df.isnull().sum().to_dict(),
        "Summary Stats": df.describe(include='all').to_dict()
    }
    return summary

summary = summarize_data(data)

# Send summary to LLM for analysis
llm_context = {
    "filename": filename,
    "columns": list(data.columns),
    "column_types": {col: str(dtype) for col, dtype in data.dtypes.items()},
    "sample_values": data.head(5).to_dict(orient='records'),
    "summary": summary,
}

llm_prompt = f"""
You are analyzing a dataset for a data scientist. Here is the context:

Filename: {llm_context['filename']}
Columns: {llm_context['columns']}
Column Types: {llm_context['column_types']}
Sample Values:
{tabulate(llm_context['sample_values'], headers="keys")}

Summary:
Shape: {llm_context['summary']['Shape']}
Missing Values: {llm_context['summary']['Missing Values']}

Suggest a few analyses to perform and visualize insights.
"""

# Query LLM using AI Proxy
def query_llm(prompt):
    try:
        url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",  # Supported chat model
            "messages": [
                {"role": "system", "content": "You are a helpful data analysis assistant. Provide insights, suggestions, and implications based on the given analysis and visualizations."},
                {"role": "user", "content": prompt},
            ],
        }
        payload_json = json.dumps(payload)
        curl_command = [
            "curl",
            "-X", "POST", url,
            "-H", f"Authorization: Bearer {AIPROXY_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", payload_json
        ]
        result = subprocess.run(curl_command, capture_output=True, text=True)
        if result.returncode == 0:
            response_data = json.loads(result.stdout)
            return response_data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in curl request: {result.stderr}")
    except Exception as e:
        print(f"Error querying AI Proxy: {e}")
        return "Error: Unable to generate narrative."
analysis_suggestions = query_llm(llm_prompt)

# Perform analyses suggested by LLM and visualize
def create_visualizations(df,output_folder):
    plots = []

    # Select numeric columns only
    numeric_data = df.select_dtypes(include=['number'])

    if numeric_data.shape[1] > 1:
        # Correlation heatmap
        plt.figure(figsize=(8, 6))
        correlation = numeric_data.corr()
        sns.heatmap(correlation, annot=True, cmap='coolwarm')
        heatmap_path = "correlation_heatmap.png"
        file_path=os.path.join(output_folder,heatmap_path)
        plt.savefig(file_path)
        plots.append(heatmap_path)
        plt.close()

    if len(numeric_data.columns) >= 1:
        # Distribution of numeric columns
        for col in numeric_data.columns[:3]:
            plt.figure()
            sns.histplot(df[col], kde=True, color='blue')
            hist_path = f"{col}_distribution.png"
            file_path=os.path.join(output_folder,hist_path)
            plt.savefig(file_path)
            plots.append(hist_path)
            plt.close()

    return plots

plot_paths = create_visualizations(data,output_folder)

# narration
narration_prompt = f"""
Here is the context of the dataset analysis:

Filename: {llm_context['filename']}
Columns: {llm_context['columns']}
Analysis Suggestions: {analysis_suggestions}

Write a story narrating the data analysis, describing the dataset, the performed analyses, and insights derived. Mention the created visualizations.
"""

def create_readme(prompt):
    try:
        url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",  # Supported chat model
            "messages": [
                {"role": "system", "content": "You are a helpful data analysis assistant. Provide insights, suggestions, and implications based on the given analysis and visualizations."},
                {"role": "user", "content": prompt},
            ],
        }
        payload_json = json.dumps(payload)
        curl_command = [
            "curl",
            "-X", "POST", url,
            "-H", f"Authorization: Bearer {AIPROXY_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", payload_json
        ]
        result = subprocess.run(curl_command, capture_output=True, text=True)
        if result.returncode == 0:
            response_data = json.loads(result.stdout)
            return response_data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in curl request: {result.stderr}")
    except Exception as e:
        print(f"Error querying AI Proxy: {e}")
        return "Error: Unable to generate narrative."

narration = create_readme(narration_prompt)


with open(os.path.join(output_folder,"README.md"), "w") as readme:
    readme.write(narration)
    for plot in plot_paths:
        readme.write(f"![{plot}]({plot})\n")

print("Analysis completed. Check README.md and generated images.")
