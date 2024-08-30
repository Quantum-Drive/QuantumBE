from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# DB Models
class UserSchema(BaseModel):
  email: str
  phonenum: str
  username: str
  password: str
  profilePath: Optional[str]
  createdAt: datetime
  lastUsed: datetime
  maxVolume: int
  
  class Config:
    from_attributes = True

class DataSchema(BaseModel):
  id: int
  name: str
  volume: int
  isEncrypted: bool
  userID: str
  isDirectory: bool
  parentID: Optional['DataSchema']
  createdAt: datetime
  extension: Optional[str]
  
  class Config:
    from_attributes = True
  
class ShareSchema(BaseModel):
  dataID: int
  receivedID: Optional[str]
  expiredTime: datetime
  
  class Config:
    from_attributes = True
    
class ExtensionSchema(BaseModel):
  extension: str
  description: Optional[str]
  note: Optional[str]
  
  class Config:
    from_attributes = True

# DB Operations
# User
class UserSchemaAdd(BaseModel):
  email: str
  phonenum: str
  username: str
  password: str

class UserSchemaUpdate(BaseModel):
  email: str
  phonenum: Optional[str]
  username: Optional[str]
  password: Optional[str]
  profileImg: Optional[str]
  lastUsed: Optional[datetime]
  
  class Config:
    from_attributes = True

# Data
class DataSchemaAdd(BaseModel):
  name: str
  resourceKey: Optional[str]
  isEncrypted: bool
  isDirectory: bool
  validationToken: Optional[str]

class DataSchemaGet(BaseModel):
  id: Optional[int]
  name: Optional[str]
  isEncrypted: Optional[bool]
  userID: str
  isDirectory: Optional[bool]
  parentID: Optional[int]
  extension: Optional[str]
  isFavorite: Optional[bool]

class DataSchemaUpdate(BaseModel):
  name: Optional[str]
  parentID: Optional[int]
  
  class Config:
    from_attributes = True

# Share

# Trashbin
class TrashSchema(BaseModel):
  id: int
  name: str
  volume: int
  isEncrypted: bool
  userID: str
  isDirectory: bool
  createdAt: datetime
  
  class Config:
    from_attributes = True

