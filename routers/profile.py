import io
import hashlib
import requests
import httpx
import numpy as np
from urllib.parse import urljoin
from PIL import Image
from typing import Optional, Annotated
from collections import namedtuple
from fastapi import APIRouter, Request, Depends, HTTPException, File, UploadFile, Query, Response
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from modules.mysql.model import User, Data
from modules.mysql.schema import UserSchema, UserSchemaUpdate
from modules.mysql.crud import dbGetUser, dbGetUsedVolume, dbUpdateUser, dbUpdateUserImage
from modules.mysql.database import getMySQLDB

from modules.common import *

from .dependencies import loginManager, DS_HOST, BASE_PATH, USER_ROOT_PATH, TRASH_PATH, TEMP_PATH

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/")
async def getProfile(user: User = Depends(loginManager),
                     db: Session = Depends(getMySQLDB)):
  try:
    del(user.__dict__["password"])
    user.__dict__["usedVolume"] = dbGetUsedVolume(db, user.email)
    if user.profileExt:
      try:
        response = requests.get(urljoin(DS_HOST, "user"), params={"userHash": hashlib.sha256(user.email.encode()).hexdigest()})
        
        if response.status_code == 200:
          user.__dict__["profileImg"] = fileUtils.bytes2DataURL(response.content, user.profileExt)
        else:
          user.__dict__["profileImg"] = None
      except requests.RequestException as e:
        user.__dict__["profileImg"] = None
    del(user.__dict__["profileExt"])
  except KeyError:
    raise HTTPException(status_code=500, detail="Failed to get user profile")

  return user

@router.put("/")
async def updateProfile(userSchemaUpdate: UserSchemaUpdate,
                  user: User = Depends(loginManager),
                  db: Session = Depends(getMySQLDB)):
  updated = dbUpdateUser(db, user, userSchemaUpdate)
  if not updated:
    raise HTTPException(status_code=400, detail="Failed to update user profile")
  
  return updated

@router.put("/image")
async def updateProfileImage(imageFile: UploadFile = File(None),
                             user: User = Depends(loginManager),
                             db: Session = Depends(getMySQLDB)):
  if imageFile and imageFile.content_type.split("/")[0] != "image":
    raise HTTPException(status_code=400, detail="Invalid file type")
  
  ext = imageFile.content_type.split("/")[1] if imageFile else None
  print(ext)
  updated = dbUpdateUserImage(db, user.email, ext)
  if not updated:
    raise HTTPException(status_code=400, detail="Failed to update user profile image")
  
  userHash = hashlib.sha256(user.email.encode()).hexdigest()
  try:
    data = await imageFile.read() if imageFile else None
    response = requests.put(urljoin(DS_HOST, "user"), params={"userHash":userHash}, data={"image":data})
    
    if response.status_code == 201:
      return Response(status_code=201)
    elif response.status_code == 204:
      return Response(status_code=204)
    else:
      raise HTTPException(status_code=response.status_code, detail=response.text)
  except requests.RequestException as e:
    raise HTTPException(status_code=500, detail=str(e))