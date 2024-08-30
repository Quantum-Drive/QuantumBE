from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .model import DataCache
from .schema import DataCacheSchema

# Cache CRUD
def dbCreateCache(db: Session, dataCache: DataCacheSchema):
  dbItem = db.query(DataCache).filter(DataCache.userHash == dataCache.userHash, 
                                      DataCache.parentID == dataCache.parentID,
                                      DataCache.fileName == dataCache.fileName).first()
  if dbItem:
    dbItem.isEncrypted = dataCache.isEncrypted
    dbItem.validationToken = dataCache.validationToken
    dbItem.inputTime = datetime.now()
    return dbItem

  dbItem = DataCache(userHash=dataCache.userHash,
                     parentID = dataCache.parentID,
                     fileName = dataCache.fileName,
                     isEncrypted=dataCache.isEncrypted,
                     validationToken=dataCache.validationToken,
                     inputTime=datetime.now())
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbGetCache(db: Session, userHash: str, validationToken: str):
  dbItem = db.query(DataCache).filter(DataCache.userHash == userHash, DataCache.validationToken == validationToken).first()
  return dbItem

def dbGetAllCache(db: Session):
  return db.query(DataCache).all()

def dbDeleteExpiredCache(db: Session):
  dbItem = db.query(DataCache).filter(DataCache.inputTime < datetime.now() - timedelta(minutes=10)).all()
  for item in dbItem:
    try:
      db.delete(item)
      db.commit()
    except SQLAlchemyError:
      db.rollback()
      pass
  return True
  
def dbDeleteCache(db: Session, userHash: str):
  try:
    dbItem = db.query(DataCache).filter(DataCache.userHash == userHash).first()
    db.delete(dbItem)
    db.commit()
    return True
  except SQLAlchemyError:
    db.rollback()
    return False
