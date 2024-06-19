from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from modules.common import fileUtils

from .model import User, Data, share
from .schema import UserSchema, DataSchema, ShareSchema
from .schema import UserSchemaAdd, UserSchemaUpdate
from .schema import DataSchemaAdd, DataSchemaGet

# User CRUD
def dbRegisterUser(db: Session, user: UserSchemaAdd):
  dbItem = User(email=user.email, 
                phonenum=user.phonenum, 
                username=user.username, 
                password=user.password,
                createdAt=datetime.now(),
                lastUsed=datetime.now())
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbGetUser(db: Session, email: str):
  dbItem = db.query(User).filter(User.email == email).first()
  return dbItem

def dbDeleteUser(db: Session, email: str):
  try:
    dbItem = db.query(User).filter(User.email == email).first()
    db.delete(dbItem)
    db.commit()
    return True
  except SQLAlchemyError:
    db.rollback()
    return False

# Data CRUD
def dbAddData(db: Session, data: DataSchemaAdd, userID: str, volume: int = None, parentID: int = None):  
  dbItem = Data(name=data.name,
                volume=volume,
                isEncrypted=data.isEncrypted,
                userID=userID,
                isDirectory=data.isDirectory,
                parentID=parentID,
                createdAt=datetime.now())
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbGetData(db: Session, data: DataSchemaGet, filterParentID: bool = False, takeAll: bool = False):
  dbItem = db.query(Data).filter(Data.userID == data.userID)
  if data.id is not None:
    dbItem = dbItem.filter(Data.id == data.id)
  if data.name:
    dbItem = dbItem.filter(Data.name == data.name)
  if data.isEncrypted is not None:
    dbItem = dbItem.filter(Data.isEncrypted == data.isEncrypted)
  if data.isDirectory is not None:
    dbItem = dbItem.filter(Data.isDirectory == data.isDirectory)
  if filterParentID:
    dbItem = dbItem.filter(Data.parentID == data.parentID)
  
  if takeAll:
    return dbItem.all()
  else:
    return dbItem.first()

def dbUpdateData(db: Session, data: DataSchema, objID: int):
  dbItem = db.query(Data).filter(Data.id == objID).first()
  if not dbItem:
    return None
  
  if data.name is not None:
    dbItem.name = data.name
  if data.volume is not None:
    dbItem.volume = data.volume
  if data.isEncrypted is not None:
    dbItem.isEncrypted = data.isEncrypted
  if data.isDirectory is not None:
    dbItem.isDirectory = data.isDirectory
  if data.parentID is not None:
    dbItem.parentID = data.parentID
  if data.createdAt is not None:
    dbItem.createdAt = data.createdAt
  
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbDeleteData(db: Session, objID: int):
  try:
    dbItem = db.query(Data).filter(Data.id == objID).first()
    db.delete(dbItem)
    db.commit()
    return True
  except SQLAlchemyError:
    db.rollback()
    return False