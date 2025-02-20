import pandas as pd
import re

def clean_film_data(input_file, output_file, invalid_file):
    """
    Clean film development data based on specific criteria and output invalid rows.
    
    Requirements:
    1. Valid film name (not "*see notes*")
    2. Valid developer listed
    3. Valid dilution listed
    4. Valid ASA/ISO listed
    5. At least one valid value in 35mm, 120, or Sheet
    6. Valid temperature listed
    """
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Define a function to check if a value is valid
    def is_valid(value):
        if pd.isna(value) or value == "" or value == "*see notes*":
            return False
        return True
    
    # Create validity mask for each criteria
    film_valid = df['Film'].apply(is_valid)
    developer_valid = df['Developer'].apply(is_valid)
    dilution_valid = df['Dilution'].apply(is_valid)
    iso_valid = df['ASA/ISO'].apply(is_valid)
    format_valid = (df['35mm'].apply(is_valid) | df['120'].apply(is_valid) | df['Sheet'].apply(is_valid))
    temp_valid = df['Temp'].apply(is_valid)
    
    # Combined validity mask
    all_valid = (
        film_valid & 
        developer_valid & 
        dilution_valid & 
        iso_valid & 
        format_valid & 
        temp_valid
    )
    
    # Get valid and invalid rows
    valid_rows = df[all_valid].copy()
    invalid_rows = df[~all_valid].copy()
    
    # Add reason columns to invalid rows
    invalid_rows['Invalid_Film'] = ~film_valid
    invalid_rows['Invalid_Developer'] = ~developer_valid
    invalid_rows['Invalid_Dilution'] = ~dilution_valid
    invalid_rows['Invalid_ISO'] = ~iso_valid
    invalid_rows['Invalid_Format'] = ~format_valid
    invalid_rows['Invalid_Temp'] = ~temp_valid
    
    # Extract clean temperature values
    def extract_temp(temp_str):
        if not isinstance(temp_str, str):
            return None
        
        # Extract numeric temperature using regex
        match = re.search(r'(\d+)[CF]', str(temp_str))
        if match:
            temp_value = float(match.group(1))
            # Convert to Celsius if in Fahrenheit
            if 'F' in temp_str.upper():
                temp_value = (temp_value - 32) * 5/9
            return round(temp_value, 1)
        return None
    
    # Apply temperature extraction to valid rows
    valid_rows['Temperature_C'] = valid_rows['Temp'].apply(extract_temp)
    
    # Save cleaned data and invalid data
    valid_rows.to_csv(output_file, index=False)
    invalid_rows.to_csv(invalid_file, index=False)
    
    return {
        'original_rows': len(df),
        'valid_rows': len(valid_rows),
        'invalid_rows': len(invalid_rows),
        'percent_kept': round(len(valid_rows) / len(df) * 100, 1)
    }

if __name__ == "__main__":
    results = clean_film_data(
        'all-film-all-developer.csv', 
        'valid_all-film-all-developer.csv',
        'invalid_data.csv'
    )
    print(f"Original dataset: {results['original_rows']} rows")
    print(f"Cleaned dataset: {results['valid_rows']} rows")
    print(f"Invalid data: {results['invalid_rows']} rows")
    print(f"Kept {results['percent_kept']}% of the original data")