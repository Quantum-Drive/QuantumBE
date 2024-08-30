import os
import io
import hashlib
import base64
import json
import pickle
import shutil
import httpx
import tarfile
import asyncio
import requests
import tempfile
from typing import Optional, Annotated
from collections import namedtuple
from collections.abc import Iterable
from urllib.parse import urljoin
from PIL import Image
from fastapi import APIRouter, Request, Depends, HTTPException, File, UploadFile, Query, Response
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from modules.common import *

from modules.mysql.model import User, Data
from modules.mysql.schema import DataSchema, DataSchemaAdd, DataSchemaGet, DataSchemaUpdate, TrashSchema
from modules.mysql.crud import dbGetUser, dbAddData, dbSearchData, dbGetData, dbUpdateData, dbUpdateDataVolume, dbDeleteData, dbGetUsedVolume, getPath, dbGetPath, dbAddShare, dbGetSharing, dbGetShared, dbDeleteShare, dbExtractDataTree, dbGetExtension, dbGetDataByFileDescription, dbAddTrash
from modules.mysql.database import getMySQLDB

from modules.sqlite.model import DataCache
from modules.sqlite.schema import DataCacheSchema
from modules.sqlite.crud import dbCreateCache, dbGetCache, dbDeleteCache
from modules.sqlite.database import getSQLiteDB

from .dependencies import loginManager, DS_HOST, BASE_PATH, USER_ROOT_PATH, TRASH_PATH, TEMP_PATH

def jsonParse(jsonStr: str):
  try:
    return json.loads(jsonStr)
  except json.JSONDecodeError:
    return None

async def getThumbnail(db: Session, user: User, fileID: int, file = None):
  extension = dbGetData(db, Data(id=fileID, userID=user.email)).extension
  tmp = dbGetExtension(db, extension)
  description = tmp.description if tmp else None
  if not description in ["image", "video", "audio", "document"]:
    return None
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  
  if not os.path.exists(f"./thumbnails/{fileID}.png"):
    if file:
      match (description):
        case "image":
          image = Image.open(io.BytesIO(file))
        case "video":
          with tempfile.NamedTemporaryFile(delete=True, suffix=f".{extension}") as tempFile:
            tempFile.write(file)
            tempFile.flush()
            image = await fileUtils.clipVideo(tempFile.name)
        case "audio":
          pass
        case "document":
          pass
      with open(f"./thumbnails/{fileID}.png", "wb") as f:
        f.write((await fileUtils.thumbnail(image)).getvalue())
        
    else:
      try:
        async with httpx.AsyncClient() as client:
          response = await client.get(urljoin(DS_HOST, "file/thumbnail"), 
                                      params={"userHash": userHash, "fileID": fileID, "description": description},
                                      timeout=None)
          response.raise_for_status()
          
          with open(f"./thumbnails/{fileID}.png", "wb") as f:
            f.write(response.content)
      except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return None
  
  return Image.open(f"./thumbnails/{fileID}.png")

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
    item["resourcekey"] = base64.b64encode(("/"+getPath(db, user.email, objID=item["parentID"])).encode('utf-8')).decode()
    del(item["parentID"])
    
    item["thumbnail"] = fileUtils.img2DataURL(await getThumbnail(db, user, item["id"]))
  
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
  content = await file.read()
  validationToken = hashlib.sha256(content).hexdigest()
  cache = dbGetCache(cacheDB, userHash, validationToken)
  if not cache:
    raise HTTPException(status_code=400, detail="Data hash mismatch")
  
  data = dbSearchData(mysqlDB, Data(name=cache.fileName, userID=user.email, parentID=cache.parentID), True)
  if data:
    raise HTTPException(status_code=400, detail="File(same name) already exists")
  
  if len(content)+dbGetUsedVolume(mysqlDB, user.email) > (defaultMaxVolume := user.maxVolume if user.maxVolume else 1024*1024*1024*50):
    raise HTTPException(status_code=400, detail=f"File size exceeds the maximum volume({defaultMaxVolume})")
  
  data = dbAddData(mysqlDB, DataSchemaAdd(name=cache.fileName,
                                          resourceKey="",
                                          isEncrypted=cache.isEncrypted,
                                          isDirectory=False,
                                          validationToken=""), user.email, len(content), cache.parentID)
  if not data:
    raise HTTPException(status_code=400, detail="Failed to insert data")
  
  await getThumbnail(mysqlDB, user, data.id, content)
  
  async def iterStream():
    try:
      async with httpx.AsyncClient() as client:
        response = await client.post(urljoin(DS_HOST, "file/"), 
                                     params={"userHash":userHash, "fileID": data.id}, 
                                     files={"file": (str(data.id), content, file.content_type)}, 
                                     timeout=None)
        response.raise_for_status()
    except httpx.RequestError as e:
      pass
  asyncio.create_task(iterStream())
  
  parentID = cache.parentID
  dbDeleteCache(cacheDB, userHash)
  
  if not dbUpdateDataVolume(mysqlDB, parentID):
    raise HTTPException(status_code=400, detail="File upload failed")
  return JSONResponse({"message": "File uploaded successfully"}, status_code=201)


@router.get("/search")
async def fileSearch(keyword: str = Query(...),
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
    item["resourcekey"] = base64.b64encode(("/"+getPath(db, user.email, objID=item["parentID"])).encode('utf-8')).decode()
    del(item["parentID"])
    item["thumbnail"] = fileUtils.img2DataURL(await getThumbnail(db, user, item["id"]))
  
  return data


@router.get("/{contentID}")
def fileDataGet(contentID: int,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  data = dbGetData(db, Data(id=contentID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  
  return data


@router.put("/{contentID}")
def fileUpdate(contentID: int,
                updateData: DataSchemaUpdate,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  srcData = dbGetData(db, Data(id=contentID, userID=user.email))
  if not srcData:
    raise HTTPException(status_code=404, detail="Data not found")
  
  updatedData = dbUpdateData(db, updateData, user.email, contentID)
  return updatedData

@router.delete("/{contentID}")
def fileDelete(contentID: int,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  data = dbGetData(db, Data(id=contentID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  try:
    response = requests.delete(urljoin(DS_HOST, "file"), params={"userHash": userHash, "fileID": data.id})
    
    if response.status_code != 204:
      raise HTTPException(status_code=response.status_code, detail=response.text)
  except requests.exceptions.RequestException as e:
    raise HTTPException(status_code=400, detail="Failed to delete data")
  
  if not dbDeleteData(db, user.email, data.id):
    raise HTTPException(status_code=500, detail="Failed to delete data")
  
  if not dbUpdateDataVolume(db, data.parentID):
    raise HTTPException(status_code=500, detail="Failed to delete data perfectly")
  
  if os.path.exists(f"./thumbnails/{contentID}.png"):
    os.remove(f"./thumbnails/{contentID}.png")
  return Response(status_code=204)


@router.get("/download/{contentID}")
async def fileDownload(contentID: int,
                 user: User = Depends(loginManager),
                 db: Session = Depends(getMySQLDB)):
  data: Data = dbGetData(db, Data(id=contentID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  try:
    async with httpx.AsyncClient() as client:
      response = await client.get(urljoin(DS_HOST, "file/"), params={"userHash":userHash, "fileID": data.id}, timeout=None)
      response.raise_for_status()
    
      async def iterStream():
        async for chunk in response.aiter_bytes(chunk_size=65536):
          yield chunk
      headers = {"Content-Disposition": f'attachment; filename="{data.name}"'}
      return StreamingResponse(iterStream(), media_type="application/octet-stream", headers=headers)
  except httpx.RequestError as e:
    raise HTTPException(status_code=400, detail=f"Failed to get the file: {e}")


@router.get("/preview/{contentID}")
async def filePreview(contentID: int,
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
    
    sPath = os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, getPath(db, user.email, objID=data.id))
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



