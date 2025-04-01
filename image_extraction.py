import fitz  # PyMuPDF
import os

def convert_pdf_to_images(pdf_path, output_dir, page_numbers):
    """Convert specific PDF pages to PNG images"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        
        for pg_num in page_numbers:
            page = doc.load_page(pg_num)
            pix = page.get_pixmap(dpi=300)
            output_path = os.path.join(output_dir, f"page_{pg_num+1}.png")
            pix.save(output_path)
            print(f"Saved page {pg_num+1} as {output_path}")
            
        return True
    except Exception as e:
        print(f"Error converting PDF: {str(e)}")
        return False

# Configuration
pdf_path = r"C:\Users\mackrish_malik\Desktop\Amandeep Code\Immunization.pdf"
output_dir = r"C:\Users\mackrish_malik\Desktop\Amandeep Code\output"
pages_to_convert = [3, 4]  # Pages 4 and 5 (0-based index)

# Run conversion
convert_pdf_to_images(pdf_path, output_dir, pages_to_convert)