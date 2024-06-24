import base64
import io

from PIL import Image
from moviepy.editor import VideoFileClip
import fitz  # PyMuPDF

def createThumbnail(imagePath, thumbnailSize=(128, 128), quality=85, format='JPEG'):
  with Image.open(imagePath) as img:
    img.thumbnail(thumbnailSize)
    
    buffered = io.BytesIO()
    if format.upper() == 'JPEG':
      img.save(buffered, format=format, quality=quality)
    elif format.upper() == 'PNG':
      img.save(buffered, format=format, compress_level=9 - (quality // 10))
    else:
      img.save(buffered, format=format)
    
    imgStr = base64.b64encode(buffered.getvalue()).decode()
    dataURL = f"data:image/{format.lower()};base64,{imgStr}"
    return dataURL

def createVideoImg(videoPath, time=1.0):
  with VideoFileClip(videoPath) as clip:
    frame = clip.get_frame(time)
    img = Image.fromarray(frame)
    
    return img

def createDataURL(filePath: str, format: str):
  with Image.open(filePath) as f:
    buffered = io.BytesIO()
    f.save(buffered, format=format)
    fileBytes = buffered.getvalue()
    
  fileStr = base64.b64encode(fileBytes).decode()
  dataURL = f"data:image/{format.lower()};base64,{fileStr}"
  return dataURL

def pdf2ImageList(pdfPath, offset=0, limit=1e9):
  lImages = []
  
  # Using PyMuPDF to open the PDF
  pdfDocument = fitz.open(pdfPath)
  pdfLast = min(offset+limit, pdfDocument.page_count)
    
  for i in range(offset, pdfLast):
    # Get the page
    page = pdfDocument.load_page(i)
    
    # Convert page to pixmap
    pixmap = page.get_pixmap()
    
    # Convert pixmap to bytes
    bImage = pixmap.tobytes()
    
    # Append image bytes to list
    lImages.append(bImage)
  
  return lImages, -1 if i >= pdfDocument.page_count else i
