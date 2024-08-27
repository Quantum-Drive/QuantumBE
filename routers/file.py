import os
import hashlib
import base64
import json
import pickle
import shutil
import tarfile
from typing import Optional, Annotated
from collections import namedtuple
from collections.abc import Iterable
from fastapi import APIRouter, Request, Depends, HTTPException, File, UploadFile, Query, Response
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from modules.common import *

from modules.mysql.model import User, Data
from modules.mysql.schema import DataSchema, DataSchemaAdd, DataSchemaGet, DataSchemaUpdate, TrashSchema
from modules.mysql.crud import dbGetUser, dbAddData, dbSearchData, dbGetData, dbUpdateData, dbUpdateDataVolume, dbDeleteData, getPath, dbGetPath, dbAddShare, dbGetSharing, dbGetShared, dbDeleteShare, dbExtractDataTree, dbGetExtension, dbGetDataByFileDescription, dbAddTrash
from modules.mysql.database import getMySQLDB

from modules.sqlite.model import DataCache
from modules.sqlite.schema import DataCacheSchema
from modules.sqlite.crud import dbCreateCache, dbGetCache, dbDeleteCache
from modules.sqlite.database import getSQLiteDB

from .dependencies import loginManager, BASE_PATH, USER_ROOT_PATH, TRASH_PATH, TEMP_PATH

def jsonParse(jsonStr: str):
  try:
    return json.loads(jsonStr)
  except json.JSONDecodeError:
    return None

def addThumbnail(db: Session, item: dict, user: User):
  target = None
  tmp = dbGetExtension(db, item["extension"])
  description = tmp.description if tmp else None

  match (description):
    case ("pdf"| "video"| "audio"| "document"| "image"):
      userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
      match (description):
        case "pdf":
          target = contentUtils.pdf2ImageList(os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, getPath(db, user, item["id"])), offset=0, limit=1)[0]
        case "video":
          target = contentUtils.img2DataURL(contentUtils.clipVideo(os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, getPath(db, user, item["id"]))), "jpeg")
        case "audio":
          target = None
        case "document":
          target = None
        case "image":
          target = contentUtils.img2DataURL(contentUtils.loadImg(os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, getPath(db, user, item["id"]))), item["extension"])
    case _:
      pass
  item["thumbnail"] = target
  
  return item

router = APIRouter(prefix="/file", tags=["File"])


@router.get("/")
async def fileInfoGet(resourcekey: str = Query(None),
                      filter: str = Query(None),
                      offset: int = Query(0),
                      limit: int = Query(None),
                      order: str = Query(None),
                      ascending: bool = Query(True),
                      user: User = Depends(loginManager),
                      db: Session = Depends(getMySQLDB)):
  
  if resourcekey:
    sPath = base64.b64decode(resourcekey).decode('utf-8')
  else:
    sPath = "/"
  flag, msg = fileUtils.isAvailablePath(sPath)
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  
  lPathData = dbGetPath(db, user.email, sPath=sPath)
  if not lPathData:
    parentID = None
  else:
    parentID = lPathData[len(lPathData)-1].id
  
  match (filter):
    case "favorite":
      data = dbSearchData(db, Data(userID=user.email, isFavorite=True), filterParentID=False)
    case "share":
      data = dbGetSharing(db, user.email)
    case "shared":
      data = dbGetShared(db, user.email)
    case "image":
      data = dbGetDataByFileDescription(db, user.email, "image")
    case "video":
      data = dbGetDataByFileDescription(db, user.email, "video")
    case "audio":
      data = dbGetDataByFileDescription(db, user.email, "audio")
    case "document":
      data = dbGetDataByFileDescription(db, user.email, "document")
    case "encrypted":
      data = dbSearchData(db, Data(userID=user.email, parentID=parentID, isEncrypted=True), filterParentID=True)  
    case "recent":
      return HTTPException(status_code=400, detail="Not implemented yet")
      pass
    case None:
      data = dbSearchData(db, Data(userID=user.email, parentID=parentID), filterParentID=True)
    case _:
      return HTTPException(status_code=400, detail="Invalid filter")
  
  
  data = dbUtils.model2dict(data)
  match (order):
    case "name":
      data.sort(key=lambda x: x["name"], reverse=not ascending)
    case "volume":
      data.sort(key=lambda x: x["volume"], reverse=not ascending)
    case "createdAt":
      data.sort(key=lambda x: x["createdAt"], reverse=not ascending)
    case "updatedAt":
      data.sort(key=lambda x: x["updatedAt"], reverse=not ascending)
    case _:
      data.sort(key=lambda x: x["name"], reverse=not ascending)
  
  data = data[offset:] if len(data) > offset else []
  data = data[:limit] if limit and len(data) > limit else data
  
  for item in data:
    item["resourcekey"] = base64.b64encode(("/"+getPath(db, user, objID=item["parentID"])).encode('utf-8')).decode()
    del(item["parentID"])
    item = addThumbnail(db, item, user)
  
  return data


@router.post("/insert")
async def fileCache(filedata: DataSchemaAdd,
                    user: User = Depends(loginManager),
                    cacheDB: Session = Depends(getSQLiteDB),
                    mysqlDB: Session = Depends(getMySQLDB)):
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  if filedata.resourceKey:
    filePath = base64.b64decode(filedata.resourceKey).decode('utf-8')
  else:
    filePath = ""
  
  if not filePath or filePath[0] != "/":
    filePath = "/" + filePath
  flag, msg = fileUtils.isAvailablePath(filePath)
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  
  flag, msg = fileUtils.isAvailableName(filedata.name)
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  lPathData = dbGetPath(mysqlDB, user.email, sPath=filePath)
  if lPathData:
    parentID = lPathData[len(lPathData)-1].id
  else:
    parentID = None
  
  data = dbSearchData(mysqlDB, Data(name=filedata.name, userID=user.email, parentID=parentID,), True)
  if data:
    raise HTTPException(status_code=400, detail="File(same name) already exists")
  if filedata.isDirectory:
    flag, msg = fileUtils.makeDir(os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, filePath[1:], filedata.name))
    if not flag:
      raise HTTPException(status_code=400, detail=msg)
    data = dbAddData(mysqlDB, filedata, user.email, 0, parentID)
  else:
    data = dbCreateCache(cacheDB, DataCacheSchema(userHash=userHash,
                                                  parentID=parentID,
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
  
  data = dbSearchData(mysqlDB, Data(name=cache.fileName, userID=user.email, parentID=cache.parentID), True)
  if data:
    raise HTTPException(status_code=400, detail="File(same name) already exists")
  
  data = dbAddData(mysqlDB, DataSchemaAdd(name=cache.fileName,
                                          resourceKey="",
                                          isEncrypted=cache.isEncrypted,
                                          isDirectory=False,
                                          validationToken=""), user.email, len(content), cache.parentID)
  if not data:
    raise HTTPException(status_code=400, detail="Failed to insert data")
  
  ########################################
  # modify later
  ########################################
  flag, msg = fileUtils.makeFile(os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, getPath(mysqlDB, user, objID=data.parentID), data.name), content)    
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  parentID = cache.parentID
  dbDeleteCache(cacheDB, userHash)
  
  if dbUpdateDataVolume(mysqlDB, parentID):
    return JSONResponse({"message": "File uploaded successfully"}, status_code=201)
  return HTTPException(status_code=400, detail="File upload failed")

@router.get("/search")
def fileSearch(keyword: str = Query(...),
               offset: int = Query(0),
               limit: int = Query(None),
               order: str = Query(None),
               ascending: bool = Query(True),
               user: User = Depends(loginManager),
               db: Session = Depends(getMySQLDB)):
  if not keyword:
    raise HTTPException(status_code=400, detail="Invalid keyword")
  
  tmp = ""
  for word in keyword.split(" "):
    if word in "%_":
      tmp += "%"
    tmp += word
  
  data = dbSearchData(db, Data(name=keyword, userID=user.email))
  if not data:
    return []
  
  data = dbUtils.model2dict(data)
  match (order):
    case "name":
      data.sort(key=lambda x: x["name"], reverse=not ascending)
    case "volume":
      data.sort(key=lambda x: x["volume"], reverse=not ascending)
    case "createdAt":
      data.sort(key=lambda x: x["createdAt"], reverse=not ascending)
    case "updatedAt":
      data.sort(key=lambda x: x["updatedAt"], reverse=not ascending)
    case _:
      data.sort(key=lambda x: x["name"], reverse=not ascending)
  
  data = data[offset:] if len(data) > offset else []
  data = data[:limit] if limit and len(data) > limit else data
  
  for item in data:
    item["resourcekey"] = base64.b64encode(("/"+getPath(db, user, objID=item["parentID"]).encode('utf-8'))).decode()
    del(item["parentID"])
    item = addThumbnail(db, item, user)
  
  return data

@router.get("/{contentID}")
def fileDownload(contentID: int,
                 user: User = Depends(loginManager),
                 db: Session = Depends(getMySQLDB)):
  data: Data = dbGetData(db, Data(id=contentID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, dbGetPath(db, user.email, objID=data.id, ))
  return FileResponse(sPath, filename=data.name)

@router.put("/{contentID}")
def fileUpdate(contentID: int,
                updateData: DataSchemaUpdate,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  updateData.id = contentID
  srcData = dbGetData(db, Data(id=contentID, userID=user.email))
  if not srcData:
    raise HTTPException(status_code=404, detail="Data not found")
  
  destPath = dbGetPath(db, updateData.parentID, user)
  pass # delete logic first

@router.delete("/{contentID}")
def fileDelete(contentID: int,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  data = dbGetData(db, Data(id=contentID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  sPath = getPath(db, user, objID=data.parentID)
  metaData = dict()
  metaData['path'] = sPath
  treeRoot = dbExtractDataTree(db, user.email, data.id, metaData)
  trash = dbAddTrash(db, data, user.email)
  with open(
    os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{trash.id}.tree"), 
    "wb") as f:
    pickle.dump(treeRoot, f)
  
  absolutePath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, sPath, data.name)
  with tarfile.open(os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{trash.id}.tar.gz"), "w:gz") as tar:
    tar.add(absolutePath, arcname=data.name)
  
  with open(
    os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{trash.id}.tree"), 
    "rb") as f:
    treeRoot = pickle.load(f)
  
  flag, msg = fileUtils.delete(os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, sPath, data.name))
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  
  if not dbDeleteData(db, data.id):
    raise HTTPException(status_code=500, detail="Failed to delete data")
  
  if not dbUpdateDataVolume(db, data.parentID):
    return HTTPException(status_code=500, detail="Failed to delete data perfectly")
  return Response(status_code=204)
  

@router.get("/{contentID}/detail")
async def fileDetailGet(contentID: int,
                        offset: int = Query(0),
                        limit: int = Query(None),
                        user: User = Depends(loginManager),
                        db: Session = Depends(getMySQLDB)):
  data: Data = dbGetData(db, Data(id=contentID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  try:
    extensionData = dbGetExtension(db, data.extension)
    
    data.description = extensionData.description
    
    sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, getPath(db, user, objID=data.id))
    match (extensionData.description):
      case "document":
        if data.extension == "pdf":
          if not limit:
            data.preview, data.next = contentUtils.pdf2ImageList(sPath, offset)
          else:
            data.preview, data.next = contentUtils.pdf2ImageList(sPath, offset, limit)
        elif data.extension == "txt":
          with open(sPath, "r") as f:
            data.preview = f.read()
        # elif data.extension in ["doc", "docx"]:
        #   data.preview = contentUtils.doc2Text(sPath)
      
      case "image":
        data.preview = contentUtils.img2DataURL(contentUtils.loadImg(sPath), data.extension)
      case "video":
        data.preview = contentUtils.img2DataURL(contentUtils.clipVideo(sPath), "jpeg")
      case _:
        data.preview = None
  except (AttributeError, IndexError, ValueError):
    data.description = None 
  
  return data



