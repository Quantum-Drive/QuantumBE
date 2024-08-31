import os
import re
import hashlib
import requests
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from modules.mysql.model import User, Data
from modules.mysql.schema import UserSchema, UserSchemaAdd
from modules.mysql.crud import dbRegisterUser, dbDeleteUser
from modules.mysql.crud import dbGetData, dbDeleteData
from modules.mysql.database import getMySQLDB

from .dependencies import loginManager, DS_HOST, getUser, BASE_PATH, USER_ROOT_PATH, TRASH_PATH

router = APIRouter(prefix="/auth", tags=["Authenticator"])

@router.post("/signup")
async def signup(Response: JSONResponse,
           userdata: UserSchemaAdd,
           db: Session = Depends(getMySQLDB)):
  if(getUser(userdata.email, db)):
    raise HTTPException(status_code=403, detail="User already exists")
  
  if len(userdata.password) < 8:
    raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
  
  pattern = re.compile(r'[!@#$%^&*(),.?":{}|<>]')
  if not pattern.search(userdata.password):
    raise HTTPException(status_code=400, detail="Password must contain at least one special character")
  
  userdata.password = hashlib.sha256(userdata.password.encode('utf-8')).hexdigest()
  
  user = dbRegisterUser(db, userdata)
  if user:
    userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
    response = requests.post(f"{DS_HOST}/user", params={"userHash": userHash})
    
    if response.status_code != 201:
      dbDeleteUser(db, user.email)
      raise HTTPException(status_code=400, detail="User registration failed")
    
    # response = JSONResponse({"message": "User created successfully"}, status_code=201)
    token = loginManager.create_access_token(data={'sub':user.email},
                                             scopes=['read:protected', 'write:protected'])
    response = JSONResponse({"access_token": token, "token_type":"bearer"}, status_code=201)
    response.set_cookie(key="access-token", value=token, httponly=True, secure=True, samesite="None")
    # response.set_cookie(key="access-token", value=token, httponly=True)
    return response
  return HTTPException(status_code=400, detail="User creation failed")

@router.post("/login")
async def login(formData: OAuth2PasswordRequestForm = Depends()):
  grant_type = formData.grant_type
  if grant_type == "password":
    username = formData.username
    password = hashlib.sha256(formData.password.encode('utf-8')).hexdigest()

    user = getUser(username)
    if not user or user.password != password:
      raise InvalidCredentialsException
    
    # 로그인 세션 생성
    # response = RedirectResponse(url="/protected", status_code=302)
    token = loginManager.create_access_token(data={'sub':user.email},
                                             scopes=['read:protected', 'write:protected'])
    # refreshToken = loginManager.create_access_token(data={'sub':user.email},
    #                                                 expires=timedelta(days=7))
    # response = JSONResponse({"access_token": token, "refresh_token": refreshToken, "token_type":"bearer"}, status_code=200)
    response = JSONResponse({"access_token": token, "token_type":"bearer"}, status_code=200)
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
  # user file dir delete part
  userHash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()
  response = requests.delete(f"{DS_HOST}/user", params={"userHash": userHash})
  
  if response.status_code != 204 or not dbDeleteUser(db, user.email):
    return HTTPException(status_code=400, detail="User deletion failed")
  
  response = Response(status_code=204)
  response.delete_cookie("access-token")
  return response
    