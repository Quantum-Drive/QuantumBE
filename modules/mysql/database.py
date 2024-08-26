from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.quantumDriveDB import HOST, PORT, ID, PW, MIN, MAX

from .model import Base

DATABASE_URL = f'mysql+mysqlconnector://{ID}:{PW}@{HOST}:{PORT}/quantumDriveDB'

def initMySQLDB():
  engine = create_engine(DATABASE_URL, pool_size=MIN, max_overflow=MAX)

  # Connect to the MySQL database
  SessionLocal = sessionmaker(autoflush=False, bind=engine)
  Base.metadata.create_all(bind=engine)
  return SessionLocal
  
SessionLocal = initMySQLDB()

def getMySQLDB():
  """
  Returns a database session.

  This function creates a new database session using the `SessionLocal` object and yields it.
  After the caller is done using the session, the session is closed.

  Yields:
    SessionLocal: A database session.

  """
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

