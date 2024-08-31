import os
import io
import re
import pickle
import hashlib
import shutil
import base64
import requests

from PIL import Image

def pathSplit(sPath="/"):
  if not sPath:
    return []
  
  lPath = re.split(r'[/|\\]', sPath)
  try:
    while True:
      lPath.remove("")
  except ValueError:
    pass
  
  return lPath

def extExtract(sFileName: str):
  if not sFileName:
    return None
  
  lFileName = sFileName.split(".")
  if len(lFileName) == 1:
    return None
  
  return lFileName[-1]

def makePickle(sPath: str, obj):
  try:
    with open(sPath, "wb") as f:
      pickle.dump(obj, f)
    return True, "Saved successfully"
  except Exception as e:
    return False, f"Failed to save the object: {e}, {sPath}"

def loadPickle(sPath: str):
  try:
    with open(sPath, "rb") as f:
      obj = pickle.load(f)
    return obj
  except Exception as e:
    return None

def isAvailablePath(sPath="/"):
  if not sPath:
    return False, "Invalid path"
  
  if len(sPath.encode('utf-8')) > 4096:
    return False, "Too long path"
  
  invalid_characters = set('/\\?%*:|"<>')
  parts = pathSplit(sPath)
  for part in parts:
    if any(char in part for char in invalid_characters):
      return False, "Invalid character in path: {part}"
  
  return True, "Valid path"

def isAvailableName(sFileName: str):
  """_summary_

  Args:
      sFileName (str): file name for checking

  Returns:
      True: 
        - Valid file name
      
      False: 
        - Invalid file name
        - Too long file name
        - Invalid character in file name
        - File already exists
  """
  if not sFileName:
    return False, "Invalid file name"

  if len(sFileName.encode('utf-8')) > 255:
    return False, "Too long file name"
  
  invalid_characters = set('/\\?%*:|"<>')
  if any(char in sFileName for char in invalid_characters):
    return False, "Invalid character in file name"
  
  return True, "Valid file name"

def img2DataURL(img: Image.Image, format: str = "PNG"):
  if not img:
    return None
  
  imgByteArr = io.BytesIO()
  img.save(imgByteArr, format=format)
  imgByteArr = imgByteArr.getvalue()
  return f"data:image/{format.lower()};base64,{base64.b64encode(imgByteArr).decode('utf-8')}"
