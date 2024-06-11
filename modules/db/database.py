from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.quantumDriveDB import HOST, PORT, ID, PW, MIN, MAX

DATABASE_URL = f'mysql+mysqlconnector://{ID}:{PW}@{HOST}:{PORT}/quantumDriveDB'
engine = create_engine(DATABASE_URL, pool_size=MIN, max_overflow=MAX)

# Connect to the MySQL database
SessionLocal = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()