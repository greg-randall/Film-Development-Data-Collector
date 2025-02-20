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
        # Check for parentheses in ASA/ISO values
        if isinstance(value, str) and ('(' in value or ')' in value):
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
    
    # Function to average ISO ranges
    def average_iso_range(iso_value):
        if not isinstance(iso_value, str):
            return iso_value
            
        # Check if the ISO value is a range (contains a hyphen)
        if '-' in iso_value:
            try:
                # Split the range and convert to integers
                parts = iso_value.split('-')
                min_iso = int(parts[0].strip())
                max_iso = int(parts[1].strip())
                
                # Calculate average and round to nearest integer
                return round((min_iso + max_iso) / 2)
            except (ValueError, IndexError):
                return iso_value
        
        return iso_value
    
    # Process ISO ranges in valid rows
    valid_rows['ASA/ISO'] = valid_rows['ASA/ISO'].apply(average_iso_range)
    
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
    
    # Process development times
    def process_dev_time(time_str):
        if not is_valid(time_str):
            return {
                'total_time': None,
                'is_two_stage': False,
                'first_stage': None,
                'second_stage': None
            }
        
        time_str = str(time_str).strip()
        
        # Check if it's a two-stage process (contains +)
        if '+' in time_str:
            # Two-stage process
            stages = time_str.split('+')
            try:
                first_stage = float(stages[0].strip())
                second_stage = float(stages[1].strip())
                return {
                    'total_time': first_stage + second_stage,
                    'is_two_stage': True,
                    'first_stage': first_stage,
                    'second_stage': second_stage
                }
            except ValueError:
                return {
                    'total_time': None,
                    'is_two_stage': True,
                    'first_stage': None,
                    'second_stage': None
                }
        
        # Check if it's a range (e.g., "10-11")
        elif '-' in time_str and not time_str.startswith('-'):
            try:
                times = time_str.split('-')
                min_time = float(times[0].strip())
                max_time = float(times[1].strip())
                # Average the range
                return {
                    'total_time': (min_time + max_time) / 2,
                    'is_two_stage': False,
                    'first_stage': None,
                    'second_stage': None
                }
            except ValueError:
                return {
                    'total_time': None,
                    'is_two_stage': False,
                    'first_stage': None,
                    'second_stage': None
                }
        
        # Single value
        else:
            try:
                time_value = float(time_str)
                return {
                    'total_time': time_value,
                    'is_two_stage': False,
                    'first_stage': None,
                    'second_stage': None
                }
            except ValueError:
                return {
                    'total_time': None,
                    'is_two_stage': False,
                    'first_stage': None,
                    'second_stage': None
                }
    
    # First determine if this is a two-stage developer
    sample_data = valid_rows.apply(
        lambda row: any('+' in str(row[col]) for col in ['35mm', '120', 'Sheet'] if is_valid(row[col])),
        axis=1
    )
    valid_rows['is_two_stage_developer'] = sample_data
    
    # Function to check if a row has different times across formats
    def has_different_times_in_row(row):
        valid_formats = [fmt for fmt in ['35mm', '120', 'Sheet'] if is_valid(row[fmt])]
        if len(valid_formats) <= 1:
            return False
        first_time = str(row[valid_formats[0]])
        return any(str(row[fmt]) != first_time for fmt in valid_formats[1:])
    
    # Check if any row has different times across formats
    any_different_times = any(valid_rows.apply(has_different_times_in_row, axis=1))
    
    # Add a flag to indicate if we need to preserve format-specific times
    valid_rows['has_format_specific_times'] = valid_rows.apply(has_different_times_in_row, axis=1)
    
    # Function to get first valid development time from any format
    def get_first_valid_time(row):
        for format_col in ['35mm', '120', 'Sheet']:
            if is_valid(row[format_col]):
                return process_dev_time(row[format_col])
        return process_dev_time(None)
    
    # Process unified development times (using first available format)
    time_data = valid_rows.apply(get_first_valid_time, axis=1)
    valid_rows['dev_total_time'] = time_data.apply(lambda x: x['total_time'])
    valid_rows['dev_first_stage'] = time_data.apply(lambda x: x['first_stage'])
    valid_rows['dev_second_stage'] = time_data.apply(lambda x: x['second_stage'])
    
    # Only process format-specific times if needed
    if any_different_times:
        for format_col in ['35mm', '120', 'Sheet']:
            # Only process rows where this format differs from others
            format_rows = valid_rows[valid_rows['has_format_specific_times']]
            if not format_rows.empty:
                time_data = format_rows[format_col].apply(process_dev_time)
                valid_rows.loc[valid_rows['has_format_specific_times'], f'{format_col}_total_time'] = time_data.apply(lambda x: x['total_time'])
                valid_rows.loc[valid_rows['has_format_specific_times'], f'{format_col}_first_stage'] = time_data.apply(lambda x: x['first_stage'])
                valid_rows.loc[valid_rows['has_format_specific_times'], f'{format_col}_second_stage'] = time_data.apply(lambda x: x['second_stage'])
    
    # Drop format-specific columns if all times are identical
    if not any_different_times:
        format_specific_columns = []
        for fmt in ['35mm', '120', 'Sheet']:
            format_specific_columns.extend([f'{fmt}_total_time', f'{fmt}_first_stage', f'{fmt}_second_stage'])
        columns_to_drop = [col for col in format_specific_columns if col in valid_rows.columns]
        if columns_to_drop:
            valid_rows = valid_rows.drop(columns=columns_to_drop)
    
    # Always drop the has_format_specific_times column
    if 'has_format_specific_times' in valid_rows.columns:
        valid_rows = valid_rows.drop(columns=['has_format_specific_times'])
    
    # Apply temperature extraction to valid rows
    valid_rows['Temperature_C'] = valid_rows['Temp'].apply(extract_temp)
    
    # Drop original time and temperature columns after processing
    columns_to_drop = ['35mm', '120', 'Sheet', 'Temp']
    if 'Notes' in valid_rows.columns:
        columns_to_drop.append('Notes')
    if 'Source URL' in valid_rows.columns:
        columns_to_drop.append('Source URL')
    
    valid_rows = valid_rows.drop(columns=columns_to_drop)
    
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