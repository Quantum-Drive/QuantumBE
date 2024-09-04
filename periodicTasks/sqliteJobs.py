import os
import hashlib
import base64
import httpx
from datetime import datetime, timedelta
from urllib.parse import urljoin

from fastapi import Depends

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from modules.sqlite.model import DataCache
from modules.sqlite.crud import dbDeleteExpiredCache, dbGetAllCache
from modules.sqlite.database import initSQLiteDB, getMemoryDBIndependent

from routers.dependencies import DS_HOST

def deleteExpiredCache():
  SessionLocal = initSQLiteDB()
  db: Session = SessionLocal()
  try:
    dbDeleteExpiredCache(db)
  finally:
    db.close()
  
  
