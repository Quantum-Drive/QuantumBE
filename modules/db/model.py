from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
  __tablename__ = 'users'
  
  email = Column(String, primary_key=True, index=True)
  phonenum = Column(String, unique=True, index=True)
  username = Column(String)
  password = Column(String)
  profilePath = Column(String)
  created_at = Column(DateTime)
  last_used = Column(DateTime)

class Data(Base):
  __tablename__ = 'data'
  
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String)
  volume = Column(Integer)
  is_encrypted = Column(Boolean)
  user_id = Column(String, ForeignKey('users.email', ondelete='CASCADE'))
  is_directory = Column(Boolean)
  parent_id = Column(Integer, ForeignKey('data.id', ondelete='CASCADE'), nullable=True)
  created_at = Column(DateTime)
  
  user = relationship('User', foreign_keys=[user_id])

class share(Base):
  __tablename__ = 'shares'
  
  src_id = Column(String, ForeignKey('users.email', ondelete='CASCADE'), primary_key=True, index=True)
  dest_id = Column(String, ForeignKey('users.email', ondelete='CASCADE'), primary_key=True, index=True)
  data_id = Column(Integer, ForeignKey('data.id', ondelete='CASCADE'), primary_key=True)
  created_at = Column(DateTime)
  
  user1 = relationship('User', foreign_keys=[src_id])
  user2 = relationship('User', foreign_keys=[dest_id])
  data = relationship('Data', foreign_keys=[data_id])

