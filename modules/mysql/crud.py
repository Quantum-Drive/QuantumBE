from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from modules.common import dbUtils, fileUtils, tree

from .model import User, Data, Share, Extension, Trash
from .schema import UserSchema, DataSchema, ShareSchema, TrashSchema
from .schema import UserSchemaAdd, UserSchemaUpdate
from .schema import DataSchemaAdd, DataSchemaGet, DataSchemaUpdate

from .schema import ExtensionSchema

# User CRUD
def dbRegisterUser(db: Session, user: UserSchemaAdd):
  dbItem = User(email=user.email, 
                phonenum=user.phonenum, 
                username=user.username, 
                password=user.password,
                createdAt=datetime.now(),
                lastUsed=datetime.now(),
                maxVolume=None)
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbGetUser(db: Session, email: str):
  dbItem = db.query(User).filter(User.email == email).first()
  return dbItem

def dbUpdateUser(db: Session, user: User, userSchemaUpdate: UserSchemaUpdate):
  dbItem = db.query(User).filter(User.email == user.email).first()
  if not dbItem:
    return None
  
  if user.phonenum is not None:
    dbItem.phonenum = userSchemaUpdate.phonenum
  if userSchemaUpdate.username is not None:
    dbItem.username = userSchemaUpdate.username
  if userSchemaUpdate.password is not None:
    dbItem.password = userSchemaUpdate.password
  if userSchemaUpdate.profileImg is not None:
    dbItem.profilePath = userSchemaUpdate.profilePath
  if userSchemaUpdate.lastUsed is not None:
    dbItem.lastUsed = userSchemaUpdate.lastUsed
  
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbGetUsedVolume(db: Session, userID: str):
  value = db.query(func.sum(Data.volume)).filter(Data.userID == userID).filter(Data.parentID == None).scalar()
  if not value:
    return 0
  return value

def dbDeleteUser(db: Session, user: User):
  try:
    dbItem = db.query(User).filter(User.email == user.email).first()
    db.delete(dbItem)
    db.commit()
    return True
  except SQLAlchemyError:
    db.rollback()
    return False

# Data CRUD
def dbAddData(db: Session, data: DataSchemaAdd, userID: str, volume: int = None, parentID: int = None):
  if data.isDirectory:
    tmp = "directory"
  else:
    tmp = data.name.split(".")
    if len(tmp) > 1:
      tmp = tmp[-1]
      extension = db.query(Extension).filter(Extension.extension == tmp).first()
      if not extension:
        extension = Extension(extension=tmp, description=None, note=None)
        db.add(extension)
        db.commit()
        db.refresh(extension)
    else:
      tmp = None
  dbItem = Data(name=data.name,
                volume=volume,
                isEncrypted=data.isEncrypted,
                userID=userID,
                isDirectory=data.isDirectory,
                parentID=parentID,
                createdAt=datetime.now(),
                extension=tmp,
                isFavorite=False)
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbSearchData(db: Session, data: DataSchemaGet, filterParentID: bool = False):
  dbItem = db.query(Data).filter(Data.userID == data.userID)
  if data.name:
    dbItem = dbItem.filter(Data.name.like("%"+data.name+"%"))
  if data.isEncrypted is not None:
    dbItem = dbItem.filter(Data.isEncrypted == data.isEncrypted)
  if data.isDirectory is not None:
    dbItem = dbItem.filter(Data.isDirectory == data.isDirectory)
  if data.extension is not None:
    dbItem = dbItem.filter(Data.extension == data.extension)
  if data.isFavorite is not None:
    dbItem = dbItem.filter(Data.isFavorite == data.isFavorite)
  if filterParentID:
    dbItem = dbItem.filter(Data.parentID == data.parentID)
  
  return dbItem.all()

def dbGetData(db: Session, data: DataSchemaGet):
  dbItem = db.query(Data).filter(Data.id == data.id, Data.userID == data.userID).first()
  return dbItem

def dbUpdateData(db: Session, data: DataSchemaUpdate, userID: str, objID: int):
  dbItem = db.query(Data).filter(Data.id == objID, Data.userID == userID).first()
  if not dbItem:
    return None
  
  if data.name is not None:
    dbItem.name = data.name
  if data.parentID is not None:
    dbItem.parentID = data.parentID
  
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbUpdateDataVolume(db: Session, objID: int):
  if objID is None:
    return True
  
  dbItem = db.query(Data).filter(Data.id == objID).first()
  if not dbItem:
    return False
  
  if dbItem.isDirectory:
    children = db.query(Data).filter(Data.parentID == objID).all()
    dbItem.volume = sum([child.volume for child in children])
    db.commit()

  return dbUpdateDataVolume(db, dbItem.parentID)

def dbDeleteData(db: Session, userID: str, objID: int):
  try:
    dbItem = db.query(Data).filter(Data.id == objID, Data.userID == userID).first()
    db.delete(dbItem)
    db.commit()
    return True
  except SQLAlchemyError as e:
    db.rollback()
    return False

def getPath(db: Session, userID: str, objID: int = None):
  return "/".join([data.name for data in dbGetPath(db, userID, objID=objID)]) if objID is not None else ""

def dbGetPath(db: Session, userID: str, objID: int = None, sPath: str = None, ):
  lPath = []
  if objID is not None:
    while True:
      dbItem = db.query(Data).filter(Data.id == objID).first()
      lPath.insert(0, dbItem)
      if dbItem.parentID is None:
        break
      
      objID = dbItem.parentID
  elif sPath is not None:
    if not sPath or sPath == "/":
      return []
  
    previousID = None
    lPathTmp = fileUtils.pathSplit(sPath)
    for dir in lPathTmp:
      data = dbSearchData(db, Data(userID=userID, isDirectory=True, name=dir, parentID=previousID))
      if not data:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Path not found")
      
      lPath.append(data[0])
      previousID = data[0].id
  
  return lPath

def dbExtractDataTree(db: Session, userID: str, dataID: int, metaData: dict):
  dbItem = db.query(Data).filter(Data.id == dataID, Data.userID == userID).first()
  if not dbItem:
    return None
  root = tree.Tree(metaData)
  dataNode = tree.Node(dataID, dbUtils.model2dict(dbItem))
  root.addChild(dataNode)
  
  if not dbItem.isDirectory:
    return root, [dataID]
  
  return root, _dbExtractDataTree(db, userID, dataNode)

def _dbExtractDataTree(db: Session, userID: str, parentNode: tree.Node):
  dbItems = db.query(Data).filter(Data.parentID == parentNode.name, Data.userID == userID).all()
  lFiles = []
  for item in dbItems:
    childNode = tree.Node(item.id, dbUtils.model2dict(item))
    parentNode.addChild(childNode)
    
    if not item.isDirectory:
      lFiles.append(item.id)
    else:
      lFiles += _dbExtractDataTree(db, userID, childNode)
  return lFiles

# Share CRUD
def dbAddShare(db: Session, share: ShareSchema, userID: str):
  dbItem = Share(dataID=share.dataID,
                receivedID=share.receivedID,
                expiredTime=share.expiredTime)
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbGetSharing(db: Session, userID: str):
  dbItems = db.query(Data, Share).filter(Data.userID == userID).join(Share, Share.dataID == Data.id).all()
  print(dbItems)
  return dbItems

def dbGetShared(db: Session, receivedID: str):
  dbItem = db.query(Data, Share).filter(Share.receivedID == receivedID).join(Data, Data.id==Share.dataID and Data.userID == receivedID).all()
  return dbItem

def dbDeleteShare(db: Session, dataID: int, receivedID: str):
  try:
    dbItem = db.query(Share).filter(Share.dataID == dataID, Share.receivedID == receivedID).first()
    db.delete(dbItem)
    db.commit()
    return True
  except SQLAlchemyError:
    db.rollback()
    return False

# Extension CRUD
def dbAddExtension(db: Session, extensionSchema: ExtensionSchema):
  dbItem = Extension(extension=extensionSchema.extension, 
                     description=extensionSchema.description, 
                     note=extensionSchema.note)
  db.add(dbItem)
  db.commit()
  db.refresh(dbItem)
  return dbItem

def dbGetExtension(db: Session, extension: str):
  dbItem = db.query(Extension).filter(Extension.extension == extension).first()
  return dbItem

def dbGetDataByFileDescription(db: Session, userID: str, description: str):
  dbItem = db.query(Data).filter(Data.userID == userID).join(Extension, Extension.extension == Data.extension, isouter=True).filter(Extension.description == description).all()
  return dbItem

def dbMatchExtension(db: Session, obj: object):
  if isinstance(obj, str):
    tmp = obj.split(".")
  elif isinstance(obj, dict):
    tmp = obj["name"].split(".") if not obj["isDirectory"] else ["directory"]
  else:
    tmp = obj.name.split(".") if not obj.isDirectory else ["directory"]
  
  if len(tmp) > 1:
    tmp = tmp[-1]
    extension = db.query(Extension).filter(Extension.extension == tmp).first()
    if not extension:
      extension = Extension(extension=tmp, description=None, note=None)
      db.add(extension)
      db.commit()
      db.refresh(extension)
    return tmp
  elif tmp[0] == "directory":
    return "directory"
  return None

# Trashbin CRUD
def dbAddTrash(db: Session, data: DataSchema, userID: str):
  try:
    dbItem = Trash(name=data.name,
                volume=data.volume,
                isEncrypted=data.isEncrypted,
                userID=userID,
                isDirectory=data.isDirectory,
                createdAt=data.createdAt)
    db.add(dbItem)
    db.commit()
  except SQLAlchemyError as e:
    db.rollback()
    return None
  
  db.refresh(dbItem)
  return dbItem

def dbGetTrash(db: Session, userID: str, id: int, ):
  dbItem = db.query(Trash).filter(Trash.id == id, Trash.userID == userID).first()
  return dbItem

def dbGetTrashAll(db: Session, userID: str):
  dbItem = db.query(Trash).filter(Trash.userID == userID).all()
  return dbItem

def dbRestoreTrash(db: Session, id: int, root: tree.Tree, userID: str):
  dbItem = db.query(Trash).filter(Trash.id == id, Trash.userID == userID).first()
  if not dbItem:
    return None, [], []
  
  parentID = dbGetPath(db, userID, sPath=root.value["path"])
  if len(parentID) > 1:
    parentID = parentID[-1].id
  elif parentID:
    parentID = parentID[0].id
  else:
    parentID = None
  
  restored, lPrevFiles, lNewFiles = _dbRestoreTrash(db, root.getChildren()[0], userID, parentID)
  if not restored:
    db.rollback()
    return None, [], []
  
  db.delete(dbItem)
  db.commit()
  db.refresh(restored)
  return restored, lPrevFiles, lNewFiles

def _dbRestoreTrash(db: Session, node: tree.Node, userID: str, parentID: int = None):
  flag = False
  lPrevFiles = []
  lNewFiles = []
  dbItems = dbSearchData(db, Data(userID=userID, name=node.value["name"], parentID=parentID), filterParentID=True)
  if dbItems:
    if not dbItems[0].isDirectory or dbItems[0].isDirectory != node.value["isDirectory"]:
      return None, [], []
    dbItem = dbItems[0]
    flag = True
  else:
    if not dbSearchData(db, Data(id=node.value["id"])):
      dbItem = Data(id=node.name,
                    name=node.value["name"],
                    volume=node.value["volume"],
                    isEncrypted=node.value["isEncrypted"],
                    userID=node.value["userID"],
                    isDirectory=node.value["isDirectory"],
                    parentID=parentID,
                    createdAt=node.value["createdAt"],
                    extension=dbMatchExtension(db, node.value),
                    isFavorite=False)
    else:
      dbItem = Data(name=node.value["name"],
                    volume=node.value["volume"],
                    isEncrypted=node.value["isEncrypted"],
                    userID=node.value["userID"],
                    isDirectory=node.value["isDirectory"],
                    parentID=parentID,
                    createdAt=node.value["createdAt"],
                    extension=dbMatchExtension(db, node.value),
                    isFavorite=False)

    db.add(dbItem)
    if not node.value["isDirectory"]:
      lPrevFiles.append(node.value["id"]) 
      lNewFiles.append(dbItem.id)
  dbItems = []
  for child in node.getChildren():
    child, lTmpPrevFiles, lTmpNewFiles = _dbRestoreTrash(db, child, userID, dbItem.id)
    if not child:
      db.rollback()
      return None, [], []
    dbItems.append(child)
    lPrevFiles += lTmpPrevFiles
    lNewFiles += lTmpNewFiles
  
  if flag:
    dbItem.volume += sum([item.volume for item in dbItems])

  return dbItem, lPrevFiles, lNewFiles

def dbDeleteTrash(db: Session, userID: str, id: int = None):
  try:
    dbQuery = db.query(Trash).filter(Trash.userID == userID)
    if id is not None:
      dbQuery = dbQuery.filter(Trash.id == id)
    dbItem = dbQuery.all()
    for item in dbItem:
      db.delete(item)
    db.commit()
    return True
  except SQLAlchemyError:
    db.rollback()
    return False