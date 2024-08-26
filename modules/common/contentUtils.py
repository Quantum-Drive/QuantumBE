import base64
import io

from PIL import Image
from moviepy.editor import VideoFileClip
import fitz  # PyMuPDF

def img2DataURL(img: Image.Image, format: str, isThumbnail=False, thumbnailSize=(128, 128), quality=85):
  buffered = io.BytesIO()
  if isThumbnail:
    img.thumbnail(thumbnailSize)
    
    if format.upper() == 'JPEG':
      img.save(buffered, format=format, quality=quality)
    elif format.upper() == 'PNG':
      img.save(buffered, format=format, compress_level=9 - (quality // 10))
    else:
      img.save(buffered, format=format)
  else:
    img.save(buffered, format=format)

  fileStr = base64.b64encode(buffered.getvalue()).decode()
  dataURL = f"data:image/{format.lower()};base64,{fileStr}"
  return dataURL

def dataURL2Img(dataURL: str):
  # Remove the data URL prefix
  imgStr = dataURL.split(",")[1]
  # Convert the base64 string to bytes
  imgBytes = base64.b64decode(imgStr)
  # Convert the bytes to an image
  img = Image.open(io.BytesIO(imgBytes))
  return img

def clipVideo(videoPath, time=1.0):
  with VideoFileClip(videoPath) as clip:
    frame = clip.get_frame(time)
    img = Image.fromarray(frame)
    
    return img

def loadImg(filePath: str):
  return Image.open(filePath)

def pdf2ImageList(pdfPath, offset=0, limit=1e9):
  lImages = []
  i = offset
  
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
    
    # Convert bytes to base64 string
    imgStr = base64.b64encode(bImage).decode('utf-8')
        
    # Determine the format
    # Determine the format based on the colorspace
    if pixmap.colorspace.name == "`DeviceRGB":
      format = "jpeg"
    elif pixmap.colorspace.name == "DeviceCMYK":
      format = "jpeg"  # CMYK is typically converted to JPEG
    elif pixmap.colorspace.name == "DeviceGray":
      format = "png"  # Grayscale images can be well-represented with PNG
    else:
      format = "png"  # Default to PNG for any other colorspaces
    
    # Create data URL
    dataURL = f"data:image/{format};base64,{imgStr}"
    # Append image bytes to list
    lImages.append(dataURL)
  
  return lImages, -1 if i >= pdfDocument.page_count-1 else i+1
