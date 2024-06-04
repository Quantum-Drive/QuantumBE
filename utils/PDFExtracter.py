import fitz  # PyMuPDF

def pdf2ImageList(pdfPath):
  lImages = []
  
  # Using PyMuPDF to open the PDF
  pdfDocument = fitz.open(pdfPath)
  
  for i in range(len(pdfDocument)):
    # Get the page
    page = pdfDocument.load_page(i)
    
    # Convert page to pixmap
    pixmap = page.get_pixmap()
    
    # Convert pixmap to bytes
    bImage = pixmap.tobytes()
    
    # Append image bytes to list
    lImages.append(bImage)
  
  return lImages

if __name__=="__main__":
  pdf_path = "../../trash.pdf"
  image_list = pdf2ImageList(pdf_path)
  for i, page in enumerate(image_list):
    with open(f"image{i}.jpg", "wb") as f:
      f.write(page)