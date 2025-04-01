import pandas as pd
import re
from collections import defaultdict

def clean_nip_schedule(file_path):
    # Read the corrupted CSV with flexible parsing
    df = pd.read_csv(file_path, header=0, on_bad_lines='skip')
    
    # Initialize clean data storage
    clean_data = []
    current_vaccine = None
    vaccine_entries = defaultdict(dict)
    
    # Vaccine mapping with primary identifiers
    vaccine_map = {
        'Hepatitis B': ['Hepatitis B', 'Hep B'],
        'Pentavalent': ['Pentavalent', 'Diphtheria', 'Pertussis', 'Tetanus', 'Hib'],
        'IPV': ['IPV', 'Polio'],
        'Pneumococcal': ['Pneumococcal', 'PCV'],
        'Td': ['Td', 'Tetanus'],
        'Measles': ['Measles'],
        'Rubella': ['Rubella'],
        'Japanese Encephalitis': ['Japanese Encephalitis', 'JE']
    }
    
    for _, row in df.iterrows():
        # Check for vaccine name in any column
        vaccine_found = None
        for col in df.columns:
            cell_value = str(row[col])
            for vaccine, patterns in vaccine_map.items():
                if any(re.search(p, cell_value, re.IGNORECASE) for p in patterns):
                    vaccine_found = vaccine
                    break
            if vaccine_found:
                break
        
        if vaccine_found:
            current_vaccine = vaccine_found
            vaccine_entries[current_vaccine] = {
                'Vaccine': current_vaccine,
                'When to give': '',
                'Dose': '',
                'Route': '',
                'Site': ''
            }
        
        if current_vaccine:
            # Clean and add information to appropriate fields
            for col in df.columns:
                clean_val = re.sub(r'[^a-zA-Z0-9\s\-/()]', '', str(row[col])).strip()
                if not clean_val:
                    continue
                
                if col == 'When to give':
                    vaccine_entries[current_vaccine]['When to give'] += ' ' + clean_val
                elif col == 'Dose':
                    vaccine_entries[current_vaccine]['Dose'] += ' ' + clean_val
                elif col == 'Route':
                    vaccine_entries[current_vaccine]['Route'] += ' ' + clean_val
                elif col == 'Site':
                    vaccine_entries[current_vaccine]['Site'] += ' ' + clean_val
                elif col == 'Vaccine' and not vaccine_found:
                    # Handle continuation lines
                    vaccine_entries[current_vaccine]['Vaccine'] += ' ' + clean_val
    
    # Post-processing
    for vaccine, entry in vaccine_entries.items():
        # Standardize dose information
        if 'dose' in entry['Dose'].lower():
            entry['Dose'] = re.sub(r'(?i)dose\s*', '', entry['Dose'])
        
        # Extract age information
        age_matches = re.findall(
            r'(\d+\s*(?:days?|weeks?|months?|years?)|at\s*birth|first\s*\d+\s*days?)', 
            entry['When to give'],
            re.IGNORECASE
        )
        if age_matches:
            entry['When to give'] = ', '.join(sorted(set(age_matches)))
        
        # Clean other fields
        for field in ['Dose', 'Route', 'Site']:
            entry[field] = re.sub(r'\s+', ' ', entry[field]).strip()
            entry[field] = re.sub(r'(?i)left\b', 'Left', entry[field])
            entry[field] = re.sub(r'(?i)right\b', 'Right', entry[field])
        
        clean_data.append(entry)
    
    return pd.DataFrame(clean_data)

# Process the file
input_path = r"C:\Users\mackrish_malik\Desktop\Amandeep Code\output\nip_schedule.csv"
output_path = r"C:\Users\mackrish_malik\Desktop\Amandeep Code\output\cleaned_nip_schedule.csv"

cleaned_df = clean_nip_schedule(input_path)

# Save cleaned data
cleaned_df.to_csv(output_path, index=False)

print("Cleaning complete. Results:")
print(cleaned_df.head().to_string(index=False))