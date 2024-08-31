import os
import pickle
import hashlib
import tarfile
import requests
import httpx
import json
import base64
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, Response, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from modules.common import tree

from modules.mysql.model import User, Data
from modules.mysql.schema import TrashSchema
from modules.mysql.crud import dbGetData, dbDeleteData, dbExtractDataTree, dbUpdateDataVolume, getPath, dbAddTrash, dbGetTrash, dbGetTrashAll, dbRestoreTrash, dbDeleteTrash
from modules.mysql.database import getMySQLDB

from .dependencies import loginManager, DS_HOST, BASE_PATH, USER_ROOT_PATH, TRASH_PATH

router = APIRouter(prefix="/trashbin", tags=["Trashbin"])

@router.get("/")
def getTrashbin(user: User = Depends(loginManager),
                 db: Session = Depends(getMySQLDB)):
  trash = dbGetTrashAll(db, user.email)
  return trash

@router.post("/")
async def fillTrashbin(request: Request,
                      # lContentID: str = Form(...),
                      lContentID: str = Form(...),
                      user: User = Depends(loginManager),
                      db: Session = Depends(getMySQLDB)):
  if not lContentID:
    raise HTTPException(status_code=400, detail="No content to delete")
  
  lContentID = json.loads(lContentID)
  statuses = {}
  # lContentID = lContentID.split(",")
  for contentID in lContentID:
    contentID = int(contentID)
    data = dbGetData(db, Data(id=contentID, userID=user.email))
    if not data:
      statuses.append({"status_code": 404, "detail": "Data not found"})
      continue
    
    userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
    metaData = dict()
    metaData["path"] = getPath(db, user.email, data.parentID)
    treeRoot, lFiles = dbExtractDataTree(db, user.email, data.id, metaData)
    trash = dbAddTrash(db, data, user.email)
    try:
        response = requests.post(urljoin(DS_HOST, "trash"), 
                                params={"userHash": userHash},
                                data={"trashID": trash.id, "lFiles": lFiles, "treePickle": base64.b64encode(pickle.dumps(treeRoot)).decode()})
        if response.status_code != 201 or not dbDeleteData(db, user.email, data.id):
          statuses[contentID] = {"status_code":response.status_code, "detail":response.text}
        else:
          statuses[contentID] = {"status_code":response.status_code, "detail":"Data deleted successfully"}
    except requests.exceptions.RequestException as e:
      dbDeleteTrash(db, user.email, trash.id)
      statuses[contentID] = {"status_code":400, "detail":"Failed to delete data"}

  return Response(content=json.dumps(statuses), status_code=207)


@router.delete("/")
async def clearTrashbin(user: User = Depends(loginManager),
                        db: Session = Depends(getMySQLDB)):
  try:
    response = requests.delete(urljoin(DS_HOST, "trash"), 
                               params={"userHash": hashlib.sha256(user.email.encode('utf-8')).hexdigest()})
    if response.status_code != 204:
      raise HTTPException(status_code=500, detail="Failed to clear trashbin")
  except requests.exceptions.RequestException as e:
    raise HTTPException(status_code=500, detail="Failed to clear trashbin")
  
  if not dbDeleteTrash(db, user.email):
    raise HTTPException(status_code=500, detail="Failed to clear trashbin")
  return Response(status_code=204)


@router.get("/{contentID}")
async def contentInfo(contentID: int,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  trash = dbGetTrash(db, user.email, contentID)
  if not trash:
    raise HTTPException(status_code=404, detail="Content not found")

  return trash

@router.put("/{contentID}")
async def restore(contentID: int,
            user: User = Depends(loginManager),
            db: Session = Depends(getMySQLDB)):
  trash = dbGetTrash(db, user.email, contentID)
  if not trash:
    raise HTTPException(status_code=404, detail="Content not found")
  
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  try:
    response = requests.get(urljoin(DS_HOST, "trash"), 
                            params={"userHash": userHash, "trashID": trash.id})
    if response.status_code != 200:
      raise HTTPException(status_code=400, detail="Failed to restore content")
    treeRoot: tree.Tree = pickle.loads(base64.b64decode(response.content))
  except requests.exceptions.RequestException as e:
    raise HTTPException(status_code=400, detail="Failed to restore content")
  
  dbItem, lPrevFiles, lNewFiles = dbRestoreTrash(db, contentID, treeRoot, user.email)
  if not dbItem:
    raise HTTPException(status_code=400, detail="Failed to restore content")
  
  try:
    response = requests.put(urljoin(DS_HOST, "trash"), 
                            params={"userHash": userHash},
                            data={"trashID": trash.id, "lPrevFiles": lPrevFiles, "lNewFiles": lNewFiles})
    if response.status_code != 201:
      raise HTTPException(status_code=response.status_code, detail=response.text)
  except requests.exceptions.RequestException as e:
    raise HTTPException(status_code=400, detail="Failed to restore content")
  
  if not dbUpdateDataVolume(db, dbItem.id):
    raise HTTPException(status_code=400, detail="Failed to update data volume")
  db.refresh(dbItem)
  
  return dbItem


@router.delete("/{contentID}")
async def delete(contentID: int,
           user: User = Depends(loginManager),
           db: Session = Depends(getMySQLDB)):
  trash = dbGetTrash(db, user.email, contentID)
  if not trash:
    raise HTTPException(status_code=404, detail="Content not found")
  
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  if not dbDeleteTrash(db, user.email, contentID):
    raise HTTPException(status_code=400, detail="Failed to delete content")
  
  os.remove(os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{contentID}.tree"))
  os.remove(os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{contentID}.tar.gz"))
  
  return Response(status_code=204)