from .model import Base
from .database import SessionLocal, engine

Base.metadata.create_all(bind=engine)

def getDB():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()