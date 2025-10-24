"""
Standalone CSV Cleaner for AutoScout24 Data
Extracts brand and top-level model from detailed car names
"""
import csv
import re
import sys


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


def clean_csv_file(input_filename: str, output_filename: str = None):
    """
    Read CSV, extract brand and model, and save cleaned version
    """
    if output_filename is None:
        output_filename = input_filename.replace('.csv', '_cleaned.csv')

    try:
        print(f"📖 Reading {input_filename}...")

        # Read the CSV
        with open(input_filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print("⚠️  No data found in CSV")
            return

        print(f"✅ Found {len(rows)} rows")
        print("🔧 Processing...")

        # Process each row
        for row in rows:
            car_model = row.get('car_model', 'N/A')
            brand, model = extract_brand_and_model(car_model)
            row['brand'] = brand
            row['model'] = model

        # Write cleaned data
        fieldnames = ['brand', 'model', 'car_model', 'price_chf', 'mileage', 'engine_power_hp',
                      'power_mode', 'production_date', 'consumption_l_per_100km', 'transmission', 'listing_url']

        with open(output_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)

        print(f"✅ Cleaned data saved to {output_filename}")

        # Show some examples
        print("\n📊 Examples of brand/model extraction:")
        for i, row in enumerate(rows[:10]):
            print(f"   {i + 1}. {row['car_model']}")
            print(f"      → Brand: {row['brand']}, Model: {row['model']}")

        # Summary statistics
        brands = {}
        models = {}
        for row in rows:
            brand = row['brand']
            model = row['model']
            brands[brand] = brands.get(brand, 0) + 1
            models[f"{brand} {model}"] = models.get(f"{brand} {model}", 0) + 1

        print(f"\n📈 Summary:")
        print(f"   Total cars: {len(rows)}")
        print(f"   Unique brands: {len(brands)}")
        print(f"   Unique models: {len(models)}")

        print(f"\n🏆 Top 5 brands:")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {brand}: {count}")

    except FileNotFoundError:
        print(f"❌ Error: File '{input_filename}' not found")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_csv.py <input_file.csv> [output_file.csv]")
        print("\nExample:")
        print("  python clean_csv.py autoscout_data_complete.csv")
        print("  python clean_csv.py autoscout_data_complete.csv cleaned_data.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    clean_csv_file(input_file, output_file)