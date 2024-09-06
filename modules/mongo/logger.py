
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

from fastapi import Request, Response

from config.mongodb import *

# @NoSQLConnect(URI, DB)
# async def insertLog(db, log):
#   collection = db.logs
#   return await collection.insert_one(log)
  
# @NoSQLConnect(URI, DB)
# async def getLogs(db):
#   collection = db.logs
  
#   cursor = collection.find({"age": {"$gte": 18}}) 
#   return await cursor.to_list(length=100)

class MongoDBLogger(object):
  def __init__(self):
    self.client = AsyncIOMotorClient(MONGODB_URI)
    self.db = self.client[DB]
  
  def __destruct__(self):
    self.client.close()

  async def logRequest(self, request: Request, response: Response, userID: str = None):
    if response.status_code >= 400:
      return
    
    logEntry = self.createLog(request.client.host, userID, request.method, request.url.path)
    return await self.db.logs.insert_one(logEntry)

  async def getLogs(self, query: dict = None):
    if not query:
      return await self.db.logs.find().sort("timestamp", -1).limit(1000).to_list(length=1000)
    
    tmp = {}
    for key, value in query.items():
      if value:
        tmp[key] = value
    
    return await self.db.logs.find(tmp).sort("timestamp", -1).limit(1000).to_list(length=1000)

  def close(self):
    self.client.close()
  
  def createLog(self, host: str = "0.0.0.0", userID: str = None, method: str = "GET", uri: str = "/"):
    return {
      "client_host": host,
      "user_id": userID,
      "method": method,
      "uri": uri,
      "timestamp": datetime.now()
    }
  
  def initQuery(self):
    return {
      "client_host": None,
      "user_id": None,
      "method": None,
      "uri": None,
      "timestamp": None
    }