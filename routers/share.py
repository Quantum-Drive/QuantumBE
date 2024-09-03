

from fastapi import APIRouter, Depends, HTTPException, Response, Form, Request
from sqlalchemy.orm import Session

from modules.mysql.model import User, Data, Share
from modules.mysql.schema import DataSchema, ShareSchema, ShareSchemaAdd
from modules.mysql.crud import dbAddShare, dbGetShare, dbDeleteShare, dbGetData
from modules.mysql.database import getMySQLDB

from .dependencies import loginManager

router = APIRouter(prefix="/share", tags=["Share"])

@router.get("/")
def getShare():
  return {"message": "Hello World"}

@router.post("/")
async def fileShare(shareSchemaAdd: ShareSchemaAdd,
                    user: User = Depends(loginManager),
                    db: Session = Depends(getMySQLDB)):
  data = dbGetData(db, Data(id=shareSchemaAdd.dataID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  
  share = dbAddShare(db, shareSchemaAdd)
  if not share:
    raise HTTPException(status_code=400, detail="Failed to share")
  return share

@router.delete("/{sharingID}")
async def fileUnshare(sharingID: int,
                      user: User = Depends(loginManager),
                      db: Session = Depends(getMySQLDB)):
  share = dbGetShare(db, Share(sharingId=sharingID))
  if not share:
    raise HTTPException(status_code=404, detail="Share not found")
  
  data = dbGetData(db, Data(id=share.dataID, userID=user.email))
  if not data:
    raise HTTPException(status_code=404, detail="Data not found")
  
  if not dbDeleteShare(db, share):
    raise HTTPException(status_code=400, detail="Failed to unshare")
  return Response(status_code=204)