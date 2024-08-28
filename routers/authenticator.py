import hashlib
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from modules.common.fileUtils import makeDir, delete

from modules.mysql.model import User, Data
from modules.mysql.schema import UserSchema, UserSchemaAdd
from modules.mysql.crud import dbRegisterUser, dbDeleteUser
from modules.mysql.crud import dbGetData, dbDeleteData
from modules.mysql.database import getMySQLDB

from .dependencies import loginManager, getUser, BASE_PATH, USER_ROOT_PATH, TRASH_PATH

router = APIRouter(prefix="/auth", tags=["Authenticator"])

@router.post("/signup")
async def signup(Response: JSONResponse,
           userdata: UserSchemaAdd,
           db: Session = Depends(getMySQLDB)):
  if(getUser(userdata.email, db)):
    raise HTTPException(status_code=403, detail="User already exists")
  
  user = dbRegisterUser(db, userdata)
  if user:
    userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
    flag, msg = makeDir(userHash, BASE_PATH, "/", "/")
    if not flag:
      raise HTTPException(status_code=400, detail=msg)

    flag, msg = makeDir(userHash, BASE_PATH, "/", USER_ROOT_PATH)
    if not flag:
      raise HTTPException(status_code=400, detail=msg)
    
    flag, msg = makeDir(userHash, BASE_PATH, "/", TRASH_PATH)
    if not flag:
      raise HTTPException(status_code=400, detail=msg)
    
    response = JSONResponse({"message": "User created successfully"}, status_code=201)
    token = loginManager.create_access_token(data={'sub':user.email},
                                             scopes=['read:protected', 'write:protected'])
    response.set_cookie(key="access-token", value=token, httponly=True, secure=True, samesite="None")
    # response.set_cookie(key="access-token", value=token, httponly=True)
    return response
  return HTTPException(status_code=400, detail="User creation failed")

@router.post("/login")
async def login(formData: OAuth2PasswordRequestForm = Depends()):
  grant_type = formData.grant_type
  if grant_type == "password":
    username = formData.username
    password = formData.password

    user = getUser(username)
    if not user or user.password != password:
      raise InvalidCredentialsException
    
    # 로그인 세션 생성
    # response = RedirectResponse(url="/protected", status_code=302)
    token = loginManager.create_access_token(data={'sub':user.email},
                                             scopes=['read:protected', 'write:protected'])
    refreshToken = loginManager.create_access_token(data={'sub':user.email},
                                                    expires=timedelta(days=7))
    # response = JSONResponse({"access_token": token, "refresh_token": refreshToken, "token_type":"bearer"}, status_code=200)
    response = JSONResponse({"message": "Login successful"}, status_code=200)
    # loginManager.set_cookie(response, token)
    response.set_cookie(key="access-token", value=token, httponly=True, secure=True, samesite="None")
    # response.set_cookie(key="access-token", value=token, httponly=True)
    return response
  else:
    raise HTTPException(status_code=400, detail="Invalid grant type")

@router.post("/find-id")
def findId():
  pass

@router.post("/forgot-password")
def forgot_password():
  # Implement your forgot password logic here
  pass

@router.post("/reset-password")
def reset_password():
  # Implement your reset password logic here
  pass

@router.delete("/logout")
def logout(user: User = Depends(loginManager)):
  response = Response(status_code=204)
  response.delete_cookie("access-token")
  return response

@router.delete("/withdraw")
async def withdraw(user: User = Depends(loginManager),
                   db: Session = Depends(getMySQLDB)):
  # db Data delete part
  dbList = dbGetData(db, Data(userID=user.email), takeAll=True)
  for data in dbList:
    try:
      dbDeleteData(db, data.id)
    except SQLAlchemyError:
      pass
  
  # user file dir delete part
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  flag, msg = delete(userHash, BASE_PATH, "/", "/")
  if not flag:
    raise HTTPException(status_code=400, detail=msg)
  
  if dbDeleteUser(db, user.email):
    response = Response(status_code=204)
    response.delete_cookie("access-token")
    return response
  else:
    return HTTPException(status_code=400, detail="User deletion failed")