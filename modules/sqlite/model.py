from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Table
class DataCache(Base):
  __tablename__ = 'dataCache'
  id = Column(Integer, primary_key=True, index=True)
  userHash = Column(String, index=True)
  parentID = Column(Integer)
  fileName = Column(String)
  isEncrypted = Column(Boolean)
  validationToken = Column(String)
  inputTime = Column(DateTime)
