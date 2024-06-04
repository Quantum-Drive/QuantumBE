import re

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

if __name__ == "__main__":
  print(pathSplit("C:/Users/username/Desktop/"))
  
