import os
import pandas as pd
from datetime import datetime
import glob

# ---------------- CONFIG ----------------
INPUT_DIR = "state_city_excels"  # Directory containing the batch files
OUTPUT_DIR = "combined_excels"   # Directory for combined output
STATE_CODE = "AZ"                # State code to combine

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- MAIN FUNCTION ----------------
def combine_state_excels(state_code):
    """
    Combines all Excel files for a given state code into one workbook
    """
    print(f"\n{'='*60}")
    print(f"Combining Excel files for state: {state_code}")
    print(f"{'='*60}\n")
    
    # Find all Excel files starting with the state code
    pattern = os.path.join(INPUT_DIR, f"{state_code}_*.xlsx")
    excel_files = glob.glob(pattern)
    
    if not excel_files:
        print(f"[!] No Excel files found for state code: {state_code}")
        print(f"    Looking for pattern: {pattern}")
        return
    
    print(f"[+] Found {len(excel_files)} Excel file(s) to combine:")
    for i, file in enumerate(excel_files, 1):
        print(f"    {i}. {os.path.basename(file)}")
    
    # Dictionary to store all city data
    # Key: city name, Value: list of business records
    combined_data = {}
    
    # Process each Excel file
    total_sheets = 0
    total_records = 0
    
    for file_path in excel_files:
        print(f"\n[+] Processing: {os.path.basename(file_path)}")
        
        try:
            # Read all sheets from the Excel file
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty:
                    continue
                df = df.fillna("NA")
                # If city already exists, append data
                if sheet_name in combined_data:
                    combined_data[sheet_name] = pd.concat(
                        [combined_data[sheet_name], df],
                        ignore_index=True
                    )
                else:
                    combined_data[sheet_name] = df
                
                total_sheets += 1
                total_records += len(df)
                print(f"    ✓ {sheet_name}: {len(df)} records")
        
        except Exception as e:
            print(f"    [ERROR] Failed to process {os.path.basename(file_path)}: {str(e)}")
            continue
    
    if not combined_data:
        print("\n[!] No data found to combine")
        return
    
    # Remove duplicates from each city
    print(f"\n[+] Removing duplicates...")
    for city in combined_data:
        before = len(combined_data[city])
        # Remove duplicates based on Google Maps URL (most reliable unique identifier)
        combined_data[city] = combined_data[city].drop_duplicates(
            subset=['Google Maps URL'],
            keep='first'
        )
        after = len(combined_data[city])
        if before != after:
            print(f"    {city}: Removed {before - after} duplicate(s)")
    
    # Create output filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Get state name from the first file
    state_name = "Unknown"
    first_file = os.path.basename(excel_files[0])
    parts = first_file.split("_")
    if len(parts) >= 2:
        state_name = parts[1]
    
    output_file = os.path.join(
        OUTPUT_DIR,
        f"{state_code}_{state_name}_COMBINED_{timestamp}.xlsx"
    )
    
    # Write combined data to Excel
    print(f"\n[+] Writing combined Excel file...")
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for city, df in sorted(combined_data.items()):
            # Ensure sheet name is valid (max 31 chars)
            sheet_name = city[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"    ✓ {city}: {len(df)} records")
    
    # Summary
    total_cities = len(combined_data)
    final_records = sum(len(df) for df in combined_data.values())
    
    print(f"\n{'='*60}")
    print(f"[✓] COMBINATION COMPLETE!")
    print(f"{'='*60}")
    print(f"Input files:      {len(excel_files)}")
    print(f"Total sheets:     {total_sheets}")
    print(f"Unique cities:    {total_cities}")
    print(f"Total records:    {final_records}")
    print(f"Duplicates removed: {total_records - final_records}")
    print(f"\nOutput file: {output_file}")
    print(f"{'='*60}\n")

# ---------------- ADVANCED: COMBINE MULTIPLE STATES ----------------
def combine_multiple_states(state_codes):
    """
    Combine Excel files for multiple state codes
    """
    for state_code in state_codes:
        combine_state_excels(state_code)
        print("\n")

# ---------------- RUN ----------------
if __name__ == "__main__":
    # Combine single state
    combine_state_excels(STATE_CODE)
    
    # OR combine multiple states at once:
    # combine_multiple_states(["FL", "CA", "TX", "NY"])