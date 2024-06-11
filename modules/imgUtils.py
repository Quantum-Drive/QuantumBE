from PIL import Image
import base64
import io

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
