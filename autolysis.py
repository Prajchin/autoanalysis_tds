# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "seaborn",
#   "matplotlib",
# ]
# ///

import sys
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Step 1: Check input file
if len(sys.argv) != 2:
    print("Usage: uv run autolysis_goodreads.py <goodreads.csv>")
    sys.exit(1)

input_file = sys.argv[1]

# Step 2: Load the dataset
try:
    df = pd.read_csv(input_file)
except Exception as e:
    print(f"Error loading the file: {e}")
    sys.exit(1)

# Step 3: Summarize the dataset
summary = {
    "shape": df.shape,
    "columns": list(df.columns),
    "missing_values": df.isnull().sum().to_dict(),
    "data_types": df.dtypes.apply(str).to_dict(),
}

print("Dataset Summary:")
print(summary)

# Step 4: Generate basic statistics
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
summary_stats = df[numeric_cols].describe().to_dict()

print("\nSummary Statistics (Numerical Columns):")
print(summary_stats)

# Step 5: Correlation heatmap
correlation_matrix = df[numeric_cols].corr()
plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm")
plt.title("Correlation Matrix")
heatmap_file = "goodreads_correlation_matrix.png"
plt.savefig(heatmap_file)
print(f"Correlation heatmap saved as {heatmap_file}")

# Step 6: Insights from ratings
df['total_ratings'] = df[['ratings_1', 'ratings_2', 'ratings_3', 'ratings_4', 'ratings_5']].sum(axis=1)
rating_distribution = df[['ratings_1', 'ratings_2', 'ratings_3', 'ratings_4', 'ratings_5']].sum()

plt.figure(figsize=(10, 6))
sns.barplot(x=rating_distribution.index, y=rating_distribution.values, palette="viridis")
plt.title("Rating Distribution")
plt.xlabel("Rating")
plt.ylabel("Count")
rating_dist_file = "goodreads_rating_distribution.png"
plt.savefig(rating_dist_file)
print(f"Rating distribution chart saved as {rating_dist_file}")

# Step 7: Analyze top authors
top_authors = df['authors'].value_counts().head(10)
plt.figure(figsize=(10, 6))
sns.barplot(x=top_authors.values, y=top_authors.index, palette="plasma")
plt.title("Top 10 Most Frequently Listed Authors")
plt.xlabel("Count")
plt.ylabel("Authors")
top_authors_file = "goodreads_top_authors.png"
plt.savefig(top_authors_file)
print(f"Top authors chart saved as {top_authors_file}")

