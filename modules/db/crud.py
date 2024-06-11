from datetime import datetime

from sqlalchemy.orm import Session

from .model import User, Data, share
from .schema import UserSchema, DataSchema, ShareSchema
from .schema import UserSchemaAdd, UserSchemaUpdate

def dbRegisterUser(db: Session, user: UserSchemaAdd):
  dbItem = User(email=user.email, 
                phonenum=user.phonenum, 
                username=user.username, 
                password=user.password,
                created_at=datetime.now(),
                last_used=datetime.now())
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbLoadUser(db: Session, email: str):
  dbItem = db.query(User).filter(User.email == email).first()
  return dbItem