from typing import Optional, Annotated
from collections import namedtuple
from fastapi import APIRouter, Request, Depends, HTTPException, File, UploadFile, Query, Response
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from modules.mysql.model import User, Data
from modules.mysql.schema import UserSchema, UserSchemaUpdate
from modules.mysql.crud import dbGetUser, dbGetUsedVolume, dbUpdateUser
from modules.mysql.database import getMySQLDB

from .dependencies import loginManager, BASE_PATH, USER_ROOT_PATH, TRASH_PATH, TEMP_PATH

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/")
def getProfile(user: User = Depends(loginManager),
               db: Session = Depends(getMySQLDB)):
  try:
    del(user.__dict__["password"])
  except KeyError:
    pass

  user.__dict__["usedVolume"] = dbGetUsedVolume(db, user.email)
  return user

@router.put("/")
def updateProfile(userSchemaUpdate: UserSchemaUpdate,
                  user: User = Depends(loginManager),
                  db: Session = Depends(getMySQLDB)):
  updated = dbUpdateUser(db, user, userSchemaUpdate)
  if not updated:
    raise HTTPException(status_code=400, detail="Failed to update user profile")
  
  return updated