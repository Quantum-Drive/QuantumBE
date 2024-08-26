
from datetime import datetime, timedelta

from fastapi import Depends

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from modules.sqlite.model import DataCache
from modules.sqlite.crud import dbDeleteExpiredCache, dbGetAllCache
from modules.sqlite.database import initSQLiteDB, getMemoryDBIndependent

def deleteExpiredCache():
  SessionLocal = initSQLiteDB()
  db: Session = SessionLocal()
  try:
    dbDeleteExpiredCache(db)
  finally:
    db.close()