from fastapi import UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# DB Models
class DataCacheSchema(BaseModel):
  userHash: str
  parentID: Optional[int]
  fileName: str
  isEncrypted: bool
  validationToken: Optional[str]
  
  class Config:
    from_attributes = True

