import os
import sys
import re
import fitz  # PyMuPDF
from PIL import Image, ImageFilter
import pytesseract
import pandas as pd

def check_dependencies():
    """Verify all required packages are installed"""
    required = {
        'fitz': 'pymupdf',
        'pytesseract': 'pytesseract',
        'PIL': 'pillow',
        'pandas': 'pandas'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Missing dependencies. Please install with:")
        print(f"pip install {' '.join(missing)}")
        sys.exit(1)

    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        print("\nTesseract OCR not found. Please install from:")
        print("https://github.com/UB-Mannheim/tesseract/wiki")
        print("Check 'Add to PATH' during installation")
        sys.exit(1)

def pdf_to_images(pdf_path, output_dir, page_numbers):
    """Convert PDF pages to high-quality PNG images"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        doc = fitz.open(pdf_path)
        images = []
        for pg_num in page_numbers:
            page = doc.load_page(pg_num)
            zoom = 2.0  # Double resolution for better OCR
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, dpi=300)
            img_path = os.path.join(output_dir, f"page_{pg_num+1}.png")
            pix.save(img_path)
            images.append(img_path)
            print(f"Saved page {pg_num+1} as {img_path}")
        return images
    except Exception as e:
        print(f"PDF conversion error: {str(e)}")
        return []

def enhance_image(image_path):
    """Improve image quality for OCR"""
    try:
        img = Image.open(image_path)
        img = img.convert('L')  # Grayscale
        # Increase contrast
        img = img.point(lambda x: 0 if x < 140 else 255)
        # Reduce noise
        img = img.filter(ImageFilter.MedianFilter(size=3))
        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)
        return img
    except Exception as e:
        print(f"Image processing error: {str(e)}")
        return None

def extract_text_from_image(image_path):
    """Perform OCR on enhanced image"""
    try:
        img = enhance_image(image_path)
        if not img:
            return []
        
        # Optimize OCR for tables
        config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        text = pytesseract.image_to_string(img, config=config)
        return [line.strip() for line in text.split('\n') if line.strip()]
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return []

def parse_nip_table(lines):
    """Extract NIP vaccination schedule"""
    schedule = []
    current_vaccine = ""
    
    for line in lines:
        # Skip headers and separators
        if "Vaccine" in line or re.match(r'^[\|+=_-]+$', line):
            continue
            
        # Split into columns
        cols = re.split(r'\s{2,}', line.strip())
        
        if len(cols) >= 4:
            current_vaccine = cols[0]
            entry = {
                'Vaccine': current_vaccine,
                'When to give': cols[1],
                'Dose': cols[2],
                'Route': cols[3],
                'Site': cols[4] if len(cols) > 4 else ''
            }
            schedule.append(entry)
        elif cols and current_vaccine:
            # Handle wrapped vaccine names
            schedule[-1]['Vaccine'] += " " + cols[0]
    
    return schedule

def parse_iap_matrix(lines):
    """Extract IAP vaccination matrix"""
    schedule = []
    age_headers = []
    in_table = False
    
    for line in lines:
        if not in_table and "Vaccine" in line and any(x in line.lower() for x in ['birth', '6w', '10w']):
            in_table = True
            age_headers = re.findall(r'\b(?:birth|\d+[wmdy])\b', line.lower())
            continue
            
        if in_table:
            if re.match(r'^[\|+=_-]+$', line):
                continue
                
            # Get vaccine name (text before first dose code)
            vaccine = re.split(r'[A-Z]{2,}\d*', line)[0].strip()
            if not vaccine:
                continue
                
            # Find all dose codes
            doses = re.finditer(r'([A-Z]{2,}\d*)', line)
            for i, dose in enumerate(doses):
                if i < len(age_headers):
                    schedule.append({
                        'Vaccine': vaccine,
                        'Age': age_headers[i],
                        'Dose': dose.group()
                    })
    
    return schedule

def save_as_csv(data, filename, output_dir):
    """Save extracted data to CSV"""
    if not data:
        print(f"No data to save for {filename}")
        return False
    
    try:
        df = pd.DataFrame(data)
        # Clean data
        df = df.applymap(lambda x: re.sub(r'[^\w\s\-/()]', '', str(x)).strip())
        
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"Saved {filename} with {len(df)} entries")
        print("Sample data:")
        print(df.head())
        return True
    except Exception as e:
        print(f"Error saving {filename}: {str(e)}")
        return False

def main():
    # Configuration
    pdf_file = r"C:\Users\mackrish_malik\Desktop\Amandeep Code\Immunization.pdf"
    output_folder = r"C:\Users\mackrish_malik\Desktop\Amandeep Code\output"
    pages_to_extract = [3, 4]  # Pages 4 and 5 (0-based)
    
    # Verify environment
    check_dependencies()
    
    # Step 1: Convert PDF to images
    print("\nConverting PDF pages to images...")
    images = pdf_to_images(pdf_file, output_folder, pages_to_extract)
    if not images:
        print("Failed to create images from PDF")
        return
    
    # Step 2: Process NIP schedule
    print("\nExtracting NIP schedule...")
    nip_text = extract_text_from_image(images[0])
    nip_data = parse_nip_table(nip_text)
    save_as_csv(nip_data, 'nip_schedule.csv', output_folder)
    
    # Step 3: Process IAP schedule
    print("\nExtracting IAP schedule...")
    iap_text = extract_text_from_image(images[1])
    iap_data = parse_iap_matrix(iap_text)
    save_as_csv(iap_data, 'iap_schedule.csv', output_folder)
    
    print("\nProcess completed successfully!")

if __name__ == "__main__":
    main()

# import os
# import re
# import pandas as pd
# import pytesseract
# from PIL import Image, ImageEnhance, ImageFilter

# class ImmunizationExtractor:
#     def __init__(self):
#         self.vaccine_patterns = [
#             ('BCG', r'BCG'),
#             ('Hepatitis B', r'Hep[ab]t?i?t?i?s? B'),
#             ('OPV', r'OPV'),
#             ('Pentavalent', r'Penta(?:valent)?'),
#             ('IPV', r'IPV'),
#             ('Rotavirus', r'Rotavirus'),
#             ('Pneumococcal', r'Pneumo(?:cocca)?l|PCV'),
#             ('Measles', r'Measles'),
#             ('Rubella', r'Rubella'),
#             ('Japanese Encephalitis', r'Japanese Encephalitis|JE'),
#             ('Vitamin A', r'Vitamin A'),
#             ('DPT', r'DPT'),
#             ('Td', r'Td')
#         ]

#     def clean_text(self, text):
#         """Clean and normalize extracted text"""
#         if not isinstance(text, str):
#             text = str(text)
#         text = re.sub(r'[^\w\s\-/()]', '', text)
#         return text.strip()

#     def enhance_image(self, image_path):
#         """Enhanced image preprocessing"""
#         try:
#             img = Image.open(image_path)
#             img = img.convert('L')
#             enhancer = ImageEnhance.Contrast(img)
#             img = enhancer.enhance(3.0)
#             img = img.filter(ImageFilter.MedianFilter(size=3))
#             img = img.point(lambda x: 0 if x < 180 else 255)
#             return img
#         except Exception as e:
#             print(f"Image processing error: {str(e)}")
#             return None

#     def extract_text(self, image_path):
#         """Robust text extraction with error handling"""
#         try:
#             img = self.enhance_image(image_path)
#             if img is None:
#                 return ""
#             custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
#             text = pytesseract.image_to_string(img, config=custom_config)
#             return text
#         except Exception as e:
#             print(f"OCR error: {str(e)}")
#             return ""

#     def parse_nip_schedule(self, text):
#         """Improved NIP table parser with robust column detection"""
#         schedule = []
#         current_entry = None
        
#         for line in text.split('\n'):
#             line = line.strip()
#             if not line:
#                 continue
                
#             # Skip headers and separators
#             if "Vaccine" in line or re.match(r'^[\|+=_-]+$', line):
#                 continue
                
#             # Find vaccine names
#             vaccine = None
#             for v_name, pattern in self.vaccine_patterns:
#                 match = re.search(pattern, line, re.IGNORECASE)
#                 if match:
#                     vaccine = v_name
#                     remaining = line[match.end():].strip()
#                     break
            
#             if vaccine:
#                 # Save previous entry if exists
#                 if current_entry:
#                     schedule.append(current_entry)
                
#                 # Split remaining text into columns
#                 parts = re.split(r'\s{2,}', remaining, maxsplit=3)
#                 current_entry = {
#                     'Vaccine': vaccine,
#                     'When to give': self.clean_text(parts[0]) if len(parts) > 0 else '',
#                     'Dose': self.clean_text(parts[1]) if len(parts) > 1 else '',
#                     'Route': self.clean_text(parts[2]) if len(parts) > 2 else '',
#                     'Site': self.clean_text(parts[3]) if len(parts) > 3 else ''
#                 }
#             elif current_entry:
#                 # Handle continuation lines
#                 if not current_entry['When to give']:
#                     current_entry['Vaccine'] += " " + self.clean_text(line)
#                 elif not current_entry['Dose']:
#                     current_entry['When to give'] += " " + self.clean_text(line)
#                 elif not current_entry['Route']:
#                     current_entry['Dose'] += " " + self.clean_text(line)
#                 elif not current_entry['Site']:
#                     current_entry['Route'] += " " + self.clean_text(line)
#                 else:
#                     current_entry['Site'] += " " + self.clean_text(line)
        
#         # Add the last entry if it exists
#         if current_entry:
#             schedule.append(current_entry)
            
#         return schedule

#     def parse_iap_schedule(self, text):
#         """Fixed IAP matrix parser with proper parentheses"""
#         schedule = []
#         age_headers = []
#         in_table = False
        
#         for line in text.split('\n'):
#             line = line.strip()
#             if not line:
#                 continue
                
#             # Find age headers
#             if not in_table and any(age in line.lower() for age in ['birth', '6w', '10w']):
#                 age_headers = re.findall(r'\b(?:birth|\d+[wmdy])\b', line.lower())
#                 in_table = True
#                 continue
                
#             if in_table:
#                 # Skip separators
#                 if re.match(r'^[\-=\+]+$', line):
#                     continue
                    
#                 # Find vaccine names
#                 vaccine = None
#                 for v_name, pattern in self.vaccine_patterns:
#                     match = re.search(pattern, line, re.IGNORECASE)
#                     if match:
#                         vaccine = v_name
#                         line = line[match.end():].strip()
#                         break
                        
#                 if vaccine and age_headers:
#                     # Find all dose codes with proper column calculation
#                     for dose in re.finditer(r'([A-Z]{2,}\d*)', line):
#                         pos = dose.start()
#                         col = min(int(pos / (len(line)/len(age_headers))), len(age_headers)-1)
#                         schedule.append({
#                             'Vaccine': vaccine,
#                             'Age': age_headers[col],
#                             'Dose': dose.group()
#                         })
        
#         return schedule

#     def save_to_csv(self, data, filename, output_dir):
#         """Save data with validation"""
#         if not data:
#             print(f"No data to save for {filename}")
#             return False
            
#         try:
#             df = pd.DataFrame(data)
#             # Clean all columns
#             for col in df.columns:
#                 df[col] = df[col].apply(self.clean_text)
            
#             os.makedirs(output_dir, exist_ok=True)
#             filepath = os.path.join(output_dir, filename)
#             df.to_csv(filepath, index=False)
#             print(f"Saved {filename} with {len(df)} entries")
#             print("First 3 entries:")
#             print(df.head(3).to_string(index=False))
#             return True
#         except Exception as e:
#             print(f"Error saving {filename}: {str(e)}")
#             return False

#     def process_schedules(self, nip_image_path, iap_image_path, output_dir):
#         """Main processing method with error handling"""
#         print("\nProcessing NIP schedule...")
#         nip_text = self.extract_text(nip_image_path)
#         print("\nExtracted NIP Text Sample:")
#         print(nip_text[:500] + "..." if len(nip_text) > 500 else nip_text)
        
#         nip_data = self.parse_nip_schedule(nip_text)
#         self.save_to_csv(nip_data, 'nip_schedule.csv', output_dir)
        
#         print("\nProcessing IAP schedule...")
#         iap_text = self.extract_text(iap_image_path)
#         print("\nExtracted IAP Text Sample:")
#         print(iap_text[:500] + "..." if len(iap_text) > 500 else iap_text)
        
#         iap_data = self.parse_iap_schedule(iap_text)
#         self.save_to_csv(iap_data, 'iap_schedule.csv', output_dir)
        
#         print("\nProcessing completed!")

# if __name__ == "__main__":
#     output_dir = r"C:\Users\mackrish_malik\Desktop\Amandeep Code\output"
#     nip_image_path = os.path.join(output_dir, "page_4.png")
#     iap_image_path = os.path.join(output_dir, "page_5.png")
    
#     if not os.path.exists(nip_image_path):
#         print(f"Error: NIP image not found at {nip_image_path}")
#     if not os.path.exists(iap_image_path):
#         print(f"Error: IAP image not found at {iap_image_path}")
    
#     extractor = ImmunizationExtractor()
#     extractor.process_schedules(nip_image_path, iap_image_path, output_dir)

