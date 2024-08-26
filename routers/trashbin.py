import os
import pickle
import hashlib
import tarfile

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from modules.common import tree

from modules.mysql.model import User, Data
from modules.mysql.schema import TrashSchema
from modules.mysql.crud import dbUpdateDataVolume, getPath, dbGetTrash, dbGetTrashAll, dbRestoreTrash, dbDeleteTrash
from modules.mysql.database import getMySQLDB

from .dependencies import loginManager, BASE_PATH, USER_ROOT_PATH, TRASH_PATH

router = APIRouter(prefix="/trashbin", tags=["Trashbin"])

@router.get("/")
def getTrashbin(user: User = Depends(loginManager),
                 db: Session = Depends(getMySQLDB)):
  trash = dbGetTrashAll(db, user.email)
  return trash

@router.delete("/")
def clearTrashbin(user: User = Depends(loginManager),
                  db: Session = Depends(getMySQLDB)):
  if not dbDeleteTrash(db, user.email):
    raise HTTPException(status_code=400, detail="Failed to clear trashbin")
  return Response(status_code=204)


@router.get("/{contentID}")
def contentInfo(contentID: int,
                user: User = Depends(loginManager),
                db: Session = Depends(getMySQLDB)):
  trash = dbGetTrash(db, user.email, contentID)
  if not trash:
    raise HTTPException(status_code=404, detail="Content not found")

  return trash
  

@router.post("/{contentID}")
def junk(contentID: int,
         user: User = Depends(loginManager),
         db: Session = Depends(getMySQLDB)):
  pass

@router.put("/{contentID}")
def restore(contentID: int,
            user: User = Depends(loginManager),
            db: Session = Depends(getMySQLDB)):
  trash = dbGetTrash(db, user.email, contentID)
  if not trash:
    raise HTTPException(status_code=404, detail="Content not found")
  
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  with open(
    os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{contentID}.tree"), 
    "rb") as f:
    treeRoot = pickle.load(f)
  
  dbItem = dbRestoreTrash(db, contentID, treeRoot, user.email)
  if not dbItem:
    raise HTTPException(status_code=400, detail="Failed to restore content")
  
  if not dbUpdateDataVolume(db, dbItem.id):
    raise HTTPException(status_code=400, detail="Failed to update data volume")
  db.refresh(dbItem)
  
  with tarfile.open(os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{contentID}.tar.gz"), "r:gz") as tar:
    tar.extractall(path=os.path.join(BASE_PATH, userHash, USER_ROOT_PATH, treeRoot.value["path"]))
  os.remove(os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{contentID}.tree"))
  os.remove(os.path.join(BASE_PATH, userHash, TRASH_PATH, f"{contentID}.tar.gz"))
  
  return dbItem


@router.delete("/{contentID}")
def delete(contentID: int,
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