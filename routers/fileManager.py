import hashlib
import base64
import json
from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from modules.common import *

from modules.mysql.model import User, Data
from modules.mysql.schema import DataSchemaAdd, DataSchemaGet, DataSchema
from modules.mysql.crud import dbGetUser, dbAddData, dbAddData, dbSearchData, dbGetData, dbUpdateData, dbSearchExtension
from modules.mysql.database import getMySQLDB

from modules.sqlite.model import DataCache
from modules.sqlite.schema import DataCacheSchema
from modules.sqlite.crud import dbCreateCache, dbGetCache, dbDeleteCache
from modules.sqlite.database import getSQLiteDB

from .dependencies import loginManager, verifyToken, BASE_PATH

def getPathID(db: Session, sPath: str, user: User):
  if not sPath or sPath == "/":
    return None
  
  previousID = None
  lPath = fileUtils.pathSplit(sPath)
  for dir in lPath:
    data = dbSearchData(db, Data(userID=user.email, isDirectory=True, name=dir, parentID=previousID))
    
    if not data:
      raise HTTPException(status_code=404, detail="Path not found")
    
    previousID = data[0].id
  
  return previousID

def jsonParse(jsonStr: str):
  print(jsonStr)
  try:
    return json.loads(jsonStr)
  except json.JSONDecodeError:
    return None

router = APIRouter(prefix="/file")

@router.get("/")
async def fileInfoGet(resourcekey: str = Query(None),
                  id: int = Query(None),
                  name: str = Query(None),
                  isEncrypted: bool = Query(None),
                  isDirectory: bool = Query(None),
                  user: User = Depends(loginManager),
                  db: Session = Depends(getMySQLDB)):
  
  if resourcekey:
    sPath = base64.b64decode(resourcekey).decode('utf-8')
  else:
    sPath = "/"
  flag, msg = fileUtils.isAvailablePath(sPath)
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  
  parentID = getPathID(db, sPath, user)
  
  data = dbSearchData(db, 
                     Data(id=id, name=name, isEncrypted=isEncrypted, userID=user.email, 
                                   isDirectory=isDirectory, parentID=parentID), 
                     filterParentID=True)
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")

  # return data
  return data

@router.get("/{contentID}/detail")
async def fileDetailGet(contentID: int,
                        offset: int = Query(0),
                        limit: int = Query(None),
                        user: User = Depends(loginManager),
                        db: Session = Depends(getMySQLDB)):
  data: Data = dbGetData(db, Data(id=contentID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  
  extension = fileUtils.extExtract(data.name)
  try:
    extensionData = dbSearchExtension(db, extension)
    
    data.extensionType = extensionData.extensionType
    if extensionData.extensionType == "pdf":
      if not limit:
        data.content, data.next = pdfExtracter.pdf2ImageList(data.content, offset)
      else:
        data.content, data.next = pdfExtracter.pdf2ImageList(data.content, offset, limit)
      
    elif extensionData.extensionType == "image":
      data.content = content
  except (AttributeError, IndexError, ValueError):
    data.extensionType = None 
  
  return data

# @router.post("/upload")
# async def fileUpload(filedata: object = Form(examples=[schema2json(DataSchemaAdd)]),
# # async def fileUpload(filedata: DataSchemaAdd = Form(...),
#                      file: Optional[UploadFile] = File(None),
#                      user: User = Depends(loginManager),
#                      db: Session = Depends(getDB)):
#   try:
#     filedataDict = json.loads(filedata)
#     filedata = DataSchemaAdd(**filedataDict)
#   except json.JSONDecodeError:
#     raise HTTPException(status_code=400, detail="Invalid JSON in filedata")
  
#   if not filedata.isDirectory:
#     if not file:
#       raise HTTPException(status_code=400, detail="File not found")
    
#     content = await file.read()
#     if filedata.validationToken != hashlib.sha256(content).hexdigest():
#       raise HTTPException(status_code=400, detail="Data hash mismatch, data has been modified during transmission")
  
#   userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
#   if filedata.resourceKey:
#     filePath = base64.b64decode(filedata.resourceKey).encode('utf-8')
#   else:
#     filePath = "/"
  
#   try:
#     flag, msg = isValidPath(filePath)
#     if not flag:
#       raise HTTPException(status_code=400, detail=msg)
    
#     flag, msg = isValidName(filedata.name)
#     if not flag:
#       raise HTTPException(status_code=400, detail=msg)

#     parentID = getPathID(db, filePath, user)
#     data = dbSearchData(db, Data(name=filedata.name, userID=user.email, parentID=parentID,))
#     if data:
#       raise HTTPException(status_code=400, detail="File(same name) already exists")
    
#     if filedata.isDirectory:
#       flag, msg = makeDir(userHash, BASE_PATH, filePath, filedata.name)
#     else:
#       flag, msg = makeFile(userHash, BASE_PATH, filePath, filedata.name, content)
    
#   except Exception as e:
#     raise e
  
#   if filedata.isDirectory:
#     data = dbAddData(db, filedata, user.email, 0, parentID)
#   else:
#     data = dbAddData(db, filedata, user.email, len(content), parentID)
#     lFilePath = pathSplit(filePath)
#     for i in range(len(lFilePath)-1, -1, -1):
#       id = getPathID(db, "/"+"/".join(lFilePath[:i]), user)
#       data = dbGetData(db, Data(id=id, userID=user.email))
#       updatedData = dbUpdateData(db, Data(volume=data.volume+len(content)), id)
      
#       if not updatedData:
#         raise HTTPException(status_code=500, detail="Failed to update volume of parent directories")
      
#   if data:
#     return JSONResponse({"message": "File uploaded successfully"}, status_code=201)
#   return HTTPException(status_code=400, detail="File upload failed")

@router.post("/insert")
async def fileCache(filedata: DataSchemaAdd,
                    user: User = Depends(loginManager),
                    cacheDB: Session = Depends(getSQLiteDB),
                    mysqlDB: Session = Depends(getMySQLDB)):
  

  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  if filedata.resourceKey:
    filePath = base64.b64decode(filedata.resourceKey).decode('utf-8')
  else:
    filePath = "/"

  flag, msg = fileUtils.isAvailablePath(filePath)
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  
  flag, msg = fileUtils.isAvailableName(filedata.name)
  if not flag:
    raise HTTPException(status_code=400, detail=msg)

  parentID = getPathID(mysqlDB, filePath, user)
  data = dbSearchData(mysqlDB, Data(name=filedata.name, userID=user.email, parentID=parentID,))
  if data:
    raise HTTPException(status_code=400, detail="File(same name) already exists")
  
  if filedata.isDirectory:
    flag, msg = fileUtils.makeDir(userHash, BASE_PATH, filePath, filedata.name)
    if not flag:
      raise HTTPException(status_code=400, detail=msg)
    data = dbAddData(mysqlDB, filedata, user.email, 0, parentID)
  else:
    data = dbCreateCache(cacheDB, DataCacheSchema(userHash=userHash,
                                                  filePath=filePath,
                                                  fileName=filedata.name, 
                                                  isEncrypted=filedata.isEncrypted, 
                                                  validationToken=filedata.validationToken))
  if not data:
    raise HTTPException(status_code=400, detail="Failed to insert data")
  
  response = JSONResponse({"message": "Data handled successfully"}, status_code=201)
  return response

@router.post("/upload")
async def fileUpload(file: Optional[UploadFile] = File(None),
                     user: User = Depends(loginManager),
                     cacheDB: Session = Depends(getSQLiteDB),
                     mysqlDB: Session = Depends(getMySQLDB)):
  if not file:
    raise HTTPException(status_code=400, detail="File not found")
  
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  cache = dbGetCache(cacheDB, userHash)
  if not cache:
    raise HTTPException(status_code=400, detail="Cache not found")
  
  content = await file.read()
  if cache.validationToken != hashlib.sha256(content).hexdigest():
    raise HTTPException(status_code=400, detail="Data hash mismatch, data has been modified during transmission")
  
  try:
    parentID = getPathID(mysqlDB, cache.filePath, user)
    data = dbSearchData(mysqlDB, Data(name=cache.fileName, userID=user.email, parentID=parentID))
    if data:
      raise HTTPException(status_code=400, detail="File(same name) already exists")
    
    flag, msg = fileUtils.makeFile(userHash, BASE_PATH, cache.filePath, cache.fileName, content)    
  except Exception as e:
    raise e
  
  data = dbAddData(mysqlDB, DataSchemaAdd(name=cache.fileName,
                                          resourceKey="",
                                          isEncrypted=cache.isEncrypted,
                                          isDirectory=False,
                                          validationToken=""), user.email, len(content), parentID)
  if not data:
    raise HTTPException(status_code=400, detail="Failed to insert data")
  dbDeleteCache(cacheDB, userHash)
  
  lFilePath = fileUtils.pathSplit(cache.filePath)
  for i in range(len(lFilePath)-1, -1, -1):
    id = getPathID(mysqlDB, "/"+"/".join(lFilePath[:i+1]), user)
    data = dbGetData(mysqlDB, Data(id=id, userID=user.email))
    updatedData = dbUpdateData(mysqlDB, Data(volume=data.volume+len(content)), id)
    
    if not updatedData:
      raise HTTPException(status_code=500, detail="Failed to update volume of parent directories")
      
  if data:
    return JSONResponse({"message": "File uploaded successfully"}, status_code=201)
  return HTTPException(status_code=400, detail="File upload failed")

@router.post("/download")
def fileDownload():
  # Logic to download a file
  pass

@router.put("/{file_id}")
def update_file(file_id: int,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  # Logic to update a specific file by ID
  pass

@router.delete("/{file_id}")
def delete_file(file_id: int,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  # Logic to delete a specific file by ID
  pass
