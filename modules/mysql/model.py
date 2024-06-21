from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Table
class User(Base):
  __tablename__ = 'users'
  
  email = Column(String, primary_key=True, index=True)
  phonenum = Column(String, unique=True, index=True)
  username = Column(String)
  password = Column(String)
  profilePath = Column(String)
  createdAt = Column(DateTime)
  lastUsed = Column(DateTime)

class Data(Base):
  __tablename__ = 'data'
  
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String)
  volume = Column(Integer)
  isEncrypted = Column(Boolean)
  userID = Column(String, ForeignKey('users.email', ondelete='CASCADE'))
  isDirectory = Column(Boolean)
  parentID = Column(Integer, ForeignKey('data.id', ondelete='CASCADE'), nullable=True)
  createdAt = Column(DateTime)
  
  user = relationship('User', foreign_keys=[userID])
  
  __table_args__ = (
    Index('idx_username_email', "userID", "name"),
  )

class Share(Base):
  __tablename__ = 'shares'
  
  dataID = Column(Integer, ForeignKey('data.id', ondelete='CASCADE'), primary_key=True)
  receivedID = Column(String, ForeignKey('users.email', ondelete='CASCADE'), primary_key=True, index=True)
  expiredTime = Column(DateTime)
  
  data = relationship('Data', foreign_keys=[dataID])
  user = relationship('User', foreign_keys=[receivedID])

class Extension(Base):
  __tablename__ = 'extensions'
  
  extension = Column(String, primary_key=True, index=True)
  extensionType = Column(String)
  note = Column(String)

# View
class UserView(Base):
  __tablename__ = 'userView'
  
  email = Column(String, primary_key=True, index=True)
  phonenum = Column(String, unique=True, index=True)
  username = Column(String)
  profilePath = Column(String)
  createdAt = Column(DateTime)
  lastUsed = Column(DateTime)