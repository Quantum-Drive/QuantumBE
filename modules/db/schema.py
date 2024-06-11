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
  created_at: datetime
  last_used: datetime
  
  class Config:
    from_attributes = True

class DataSchema(BaseModel):
  id: int
  name: str
  volume: int
  is_encrypted: bool
  user_id: str
  is_directory: bool
  parent_id: Optional['DataSchema']
  created_at: datetime
  
  class Config:
    from_attributes = True
  
class ShareSchema(BaseModel):
  src_id: str
  dest_id: Optional[str]
  data_id: int
  duration: datetime
  
  class Config:
    from_attributes = True

# DB Operations
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
  profilePath: Optional[str]
  last_used: Optional[datetime]
  
  class Config:
    from_attributes = True
  
