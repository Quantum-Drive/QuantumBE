from datetime import timedelta

from fastapi import Depends
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException

from sqlalchemy.orm import Session

from modules.mysql.database import SessionLocal
from modules.mysql.model import User

BASE_PATH = "/data/quantumDrive/files"
USER_ROOT_PATH = "root"
TRASH_PATH = "trash"
TEMP_PATH = "temp"
SECRET = "super-secret-key"
loginManager = LoginManager(SECRET, token_url="/auth/login", 
                            use_cookie=True, 
                            default_expiry=timedelta(hours=3))

@loginManager.user_loader()
def getUser(email: str, db: Session = None):
  if not db:
    with SessionLocal() as db:
      return db.query(User).filter(User.email == email).first()
  return db.query(User).filter(User.email == email).first()
