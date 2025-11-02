"""
Combined CSV Cleaner and Model Standardizer for AutoScout24 Data
1. Extracts brand and top-level model from detailed car names
2. Standardizes model names using replacement dictionary
"""
import csv
import re
import sys
from pathlib import Path
import pandas as pd


def extract_brand_and_model(car_model: str) -> tuple:
    """
    Extract brand and top-level model from detailed car name

    Examples:
    "BMW X6M Competition (CH) FACELIFT INDIVIDUAL" → ("BMW", "X6M")
    "Mercedes-Benz EQB 350 AMG Line 4Matic" → ("Mercedes-Benz", "EQB")
    "VW Golf 2.0 TDI R-Line Aut" → ("VW", "Golf")
    "Peugeot 2008 1.2 PureTech Allure" → ("Peugeot", "2008")
    """
    if not car_model or car_model == "N/A":
        return ("N/A", "N/A")

    # Common brand mappings and their patterns
    brand_patterns = {
        'BMW': r'^BMW\s+',
        'Mercedes-Benz': r'^Mercedes-Benz\s+',
        'Mercedes': r'^Mercedes\s+',
        'Audi': r'^Audi\s+',
        'VW': r'^VW\s+',
        'Volkswagen': r'^Volkswagen\s+',
        'Porsche': r'^Porsche\s+',
        'Tesla': r'^Tesla\s+',
        'Volvo': r'^Volvo\s+',
        'Ford': r'^Ford\s+',
        'Toyota': r'^Toyota\s+',
        'Honda': r'^Honda\s+',
        'Mazda': r'^Mazda\s+',
        'Nissan': r'^Nissan\s+',
        'Hyundai': r'^Hyundai\s+',
        'Kia': r'^Kia\s+',
        'Seat': r'^Seat\s+',
        'Skoda': r'^Skoda\s+',
        'Peugeot': r'^Peugeot\s+',
        'Renault': r'^Renault\s+',
        'Citroën': r'^Citroën\s+',
        'Citroen': r'^Citroen\s+',
        'Opel': r'^Opel\s+',
        'Fiat': r'^Fiat\s+',
        'Alfa Romeo': r'^Alfa Romeo\s+',
        'Jeep': r'^Jeep\s+',
        'Land Rover': r'^Land Rover\s+',
        'Range Rover': r'^Range Rover\s+',
        'Jaguar': r'^Jaguar\s+',
        'Mini': r'^Mini\s+',
        'MINI': r'^MINI\s+',
        'Smart': r'^Smart\s+',
        'Subaru': r'^Subaru\s+',
        'Suzuki': r'^Suzuki\s+',
        'Mitsubishi': r'^Mitsubishi\s+',
        'Lexus': r'^Lexus\s+',
        'Infiniti': r'^Infiniti\s+',
        'Cupra': r'^Cupra\s+',
        'DS': r'^DS\s+',
    }

    # Find the brand
    brand = "N/A"
    remaining_text = car_model

    for brand_name, pattern in brand_patterns.items():
        match = re.search(pattern, car_model, re.IGNORECASE)
        if match:
            brand = brand_name
            remaining_text = car_model[match.end():].strip()
            break

    # If no brand found, use first word as brand
    if brand == "N/A":
        parts = car_model.split()
        if parts:
            brand = parts[0]
            remaining_text = ' '.join(parts[1:])

    # Extract top-level model (first word or first meaningful token)
    if not remaining_text:
        return (brand, "N/A")

    # Split by spaces and common separators
    tokens = re.split(r'[\s\-]+', remaining_text)

    # Get the first token as the base model
    if tokens:
        base_model = tokens[0]

        # Check if second token is numeric (part of model like "X5", "A4", "Golf 8")
        if len(tokens) > 1:
            second_token = tokens[1].lower()
            # If it's a number or starts with a number, include it
            if second_token.isdigit() or (len(second_token) > 0 and second_token[0].isdigit()):
                base_model = f"{tokens[0]} {tokens[1]}"

        return (brand, base_model)

    return (brand, "N/A")


def standardize_models(df):
    """
    Standardize model names using replacement dictionary
    """
    # Dictionary mapping search terms to correct model names
    model_replacements = {
        'AUDI e-tron': 'e-tron',
        'AUDI 2.0 TDI': '2.0 TDI',
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
        'TESLA TESLA Model 3 Performance, 513 PS': 'Model 3',
        'TESLA Signature Sport': 'Roadster',
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
    return df


def clean_and_standardize_csv(input_filename, output_filename=None):
    """
    Read CSV, extract brand and model, standardize models, and save cleaned version
    """
    input_path = Path(input_filename)
    if output_filename is None:
        output_filename = input_path.with_name(f"cleaned_{input_path.name}")
    else:
        output_filename = Path(output_filename)

    try:
        print(f"📖 Reading {input_path}...")

        # Read the CSV
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print("⚠️  No data found in CSV")
            return

        print(f"✅ Found {len(rows)} rows")
        print("🔧 Step 1: Extracting brands and models...")

        # Process each row to extract brand and model
        for row in rows:
            car_model = row.get('car_model', 'N/A')
            brand, model = extract_brand_and_model(car_model)
            row['brand'] = brand
            row['model'] = model

        # Convert to DataFrame for standardization
        fieldnames = ['brand', 'model', 'car_model', 'price_chf', 'mileage', 'engine_power_hp',
                      'power_mode', 'production_date', 'consumption_l_per_100km', 'transmission', 'listing_url']

        df = pd.DataFrame(rows)

        print("🔧 Step 2: Standardizing model names...")

        # Apply model standardization
        df = standardize_models(df)

        # Write cleaned and standardized data
        df[fieldnames].to_csv(output_filename, index=False)

        print(f"✅ Cleaned and standardized data saved to {output_filename}")

        # Show some examples
        print("\n📊 Examples of brand/model extraction and standardization:")
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            print(f"   {i + 1}. {row['car_model']}")
            print(f"      → Brand: {row['brand']}, Model: {row['model']}")

        # Summary statistics
        brands = df['brand'].value_counts().to_dict()
        models = (df['brand'] + ' ' + df['model']).value_counts().to_dict()

        print(f"\n📈 Summary:")
        print(f"   Total cars: {len(df)}")
        print(f"   Unique brands: {len(brands)}")
        print(f"   Unique models: {len(models)}")

        print(f"\n🏆 Top 5 brands:")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {brand}: {count}")

    except FileNotFoundError:
        print(f"❌ Error: File '{input_path}' not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Hardcoded paths - update these to match your project structure
        script_dir = Path(__file__).resolve().parent
        default_input = script_dir.parent / "Scraping" / "autoscout_data_complete.csv"
        default_output = script_dir / "Autoscout_Cleaned_Standardized.csv"

        # Check if file exists
        if not default_input.exists():
            print(f"❌ Error: Input file not found at: {default_input}")
            print("\n💡 Usage:")
            print(f"   python {Path(__file__).name} <input_file.csv> [output_file.csv]")
            print("\n   Example:")
            print(f"   python {Path(__file__).name} /path/to/autoscout_data_complete.csv")
            sys.exit(1)

        print("ℹ️  No input provided. Using defaults:")
        print(f"   Input:  {default_input}")
        print(f"   Output: {default_output}")

        clean_and_standardize_csv(default_input, default_output)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

        clean_and_standardize_csv(input_file, output_file)