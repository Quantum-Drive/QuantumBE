import os
import re
import pickle
import hashlib
import shutil

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

def makeDir(sFilePath: str):
  if not sFilePath:
    return False, "Invalid path"
  if os.path.exists(sFilePath):
    return False, "Directory already exists"
  
  os.makedirs(sFilePath)
  print(sFilePath)
  return True, "Directory created successfully"

def makeFile(sFilePath:str, content: bytes):
  if not sFilePath:
    return False, "Invalid path"
  
  if os.path.exists(sFilePath):
    return False, "File already exists"
  
  with open(sFilePath, "wb") as file:
    file.write(content)
  return True, "File saved successfully"

def moveFile(userHash: str, basePath: str, srcPath: str, srcName: str, destPath: str = None, destName: str = None):
  if not srcPath or not srcName:
    return False, "Invalid path or file name"
  
  if not os.path.exists(f"{basePath}/{userHash}{srcPath}/{srcName}"):
    return False, "File does not exist"
  
  if not destPath and not destName:
    return False, "Both destination path and file name are not provided"
  
  if not destPath:
    destPath = srcPath
  if not destName:
    destName = srcName

  if not os.path.exists(f"{basePath}/{userHash}{destPath}"):
    return False, "Destination path does not exist"
  
  if os.path.exists(f"{basePath}/{userHash}{destPath}/{destName}"):
    return False, "File already exists in destination"

  os.rename(f"{basePath}/{userHash}{srcPath}/{srcName}", f"{basePath}/{userHash}{destPath}/{destName}")
  return True, "File moved successfully"

def delete(sPath: str):
  if not sPath:
    return False, "Invalid path"
  
  if not os.path.exists(sPath):
    return False, f"Object does not exist {sPath}"
  
  try:
    try:
      os.remove(sPath)
    except IsADirectoryError:
      shutil.rmtree(sPath)
  except Exception as e:    
    return False, f"Failed to delete the object {e}"
  return True, "Object deleted successfully"


  
  
