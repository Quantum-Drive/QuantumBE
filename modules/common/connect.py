import asyncio
from functools import wraps
from motor.motor_asyncio import AsyncIOMotorClient

def NoSQLConnect(uri, DBName):
  def decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
      try:
        client = AsyncIOMotorClient(uri)
        db = client[DBName]
        
        return await func(db, *args, **kwargs)
      finally:
        client.close()
    return wrapper
  return decorator
