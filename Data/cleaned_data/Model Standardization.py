#Model Standardization
import csv
import sys
import pandas as pd

df = pd.read_csv("cleaned_autoscout_data_complete.csv")

# Dictionary mapping search terms to correct model names
model_replacements = {
    'AUDI e-tron': 'e-tron',
    'AUDI 2.0 TDI': ' 2.0 TDI',
    '6.0 Double Six': '6.0',
    '4x4 Country Club': '4x4 Country Club',
    'FORD S-Max': 'S-Max',
    'FORD C-Max': 'C-Max',
    'JAGUAR I-Pace': 'I-Pace',
    'Grand Cherokee': 'Grand Cherokee',
    'Range Rover Evoque 2.0': 'Range Rover Evoque 2.0',
    'MERCEDES-BENZ A AMG 45 S 4Matic+ 8G-DCT': 'A AMG',
    'i MiEV': 'i MiEV',
    '9-3 2.0i': '9-3 2.0i',
    'Smart #5 100kWh': '#5',
    'Smart #1 66': '#1',
    'TESLA Model Y': 'Model Y',
    'TESLA TESLA Model 3 Performance, 513 PS' : 'Model 3',
    'TESLA Signature Sport': 'Rodster',
    'TESLA Model S': 'Model S',
    'Toyota C-HR': 'C-HR',
    'T-Cross': 'T-Cross',
    'VW R-Line 3.0': 'R-Line 3.0',
    'T-Roc': 'T-Roc',
    'New Beetle Cabrio': 'Beetle Cabrio',
    'Käfer Cabriolet': 'Beetle Cabrio',
    'e-Golf': 'e-Golf'
}

# Apply all replacements
def assign_model(row):
    car_model_str = str(row['car_model'])
    for search_term, correct_model in model_replacements.items():
        if search_term in car_model_str:
            return correct_model
    return row['model']  # Keep original if no match

df['model'] = df.apply(assign_model, axis=1)

df.to_csv("cleaned_autoscout_data_complete.csv", index=False)