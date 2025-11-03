"""RQ3: How does the relationship between commodity prices and used car values vary across popular car brands in Switzerland? We will segment
our analysis by brand to determine whether luxury manufacturers, producers, or specific market segments exhibit different sensitivities
to raw material cost pressures."""

import pandas as pd
import os
from pathlib import Path
#%% Cell 1 Load Data
# Get script location
script_dir = Path(__file__).parent

# Define relative paths from the script's location
data_dir = script_dir.parent.parent / "Data" / "Final Data"
path_autoscout = data_dir / "Autoscout_Cleaned_Standardized.csv"
path_yahoo = data_dir / "yahoo_spot_cleaned.csv"

# Print debug info
print("Script directory:", script_dir.absolute())
print("Data directory:", data_dir.absolute())
print("Looking for files:")
print(f"- {path_autoscout.absolute()}")
print(f"- {path_yahoo.absolute()}")
print("\nIf files are not found, please check the paths above and ensure the files exist.")

try:
    # Load the data
    df1 = pd.read_csv(path_autoscout)
    df2 = pd.read_csv(path_yahoo)
    
    # Data inspection
    print("Autoscout Data (first 5 rows):")
    print(df1.head())
    print("\nYahoo Commodity Data (first 5 rows):")
    print(df2.head())
    
except FileNotFoundError as e:
    print(f"Error: {e}")
    print(f"File not found, current working directory: {os.getcwd()}")
    print(f"Looking for files at:")
    print(f"- {path_autoscout.absolute()}")
    print(f"- {path_yahoo.absolute()}")

#%% Cell 2 Data Inspection