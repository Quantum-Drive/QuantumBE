import base64
import io

from PIL import Image
from moviepy.editor import VideoFileClip


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

