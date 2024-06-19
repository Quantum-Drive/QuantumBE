import os
import re
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

def makeDir(userHash: str, basePath: str, filePath: str, dirName: str = "/"):
  if not filePath:
    return False, "Invalid path"
  
  if os.path.exists(f"{basePath}/{userHash}{filePath}/{dirName}"):
    return False, "Directory already exists"
  
  os.makedirs(f"{basePath}/{userHash}{filePath}/{dirName}")
  return True, "Directory created successfully"

def makeFile(userHash: str, basePath: str, filePath: str, fileName: str, content: bytes):
  if not filePath or not fileName:
    return False, "Invalid path or file name"
  
  if os.path.exists(f"{basePath}/{userHash}{filePath}/{fileName}"):
    return False, "File already exists"
  
  with open(f"{basePath}/{userHash}{filePath}/{fileName}", "wb") as file:
    file.write(content)
  return True, "File saved successfully"

def deleteDir(userHash: str, basePath: str, filePath: str, dirName: str = "/"):
  if not filePath:
    return False, "Invalid path"
  
  if not os.path.exists(f"{basePath}/{userHash}{filePath}/{dirName}"):
    return False, "Directory does not exist"
  
  try:
    shutil.rmtree(f"{basePath}/{userHash}{filePath}/{dirName}")
  except Exception as e:
    return False, f"Failed to delete directory: {e}"
  return True, "Directory deleted successfully"

def deleteFile(userHash: str, basePath: str, filePath: str, fileName: str):
  if not filePath or not fileName:
    return False, "Invalid path or file name"
  
  if not os.path.exists(f"{basePath}/{userHash}{filePath}/{fileName}"):
    return False, "File does not exist"
  
  os.remove(f"{basePath}/{userHash}{filePath}/{fileName}")
  return True, "File deleted successfully"

if __name__ == "__main__":
  flag, msg = makeDir(hashlib.sha256("juhy0987@naver.com".encode('utf-8')).hexdigest(),
            "/data/quantumDrive/files",
            "/", "/")
  print(msg)
  
  
