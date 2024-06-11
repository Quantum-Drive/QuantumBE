from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

from sqlalchemy.orm import Session

from modules.db.schema import UserSchema, UserSchemaAdd
from modules.db.crud import dbRegisterUser
from modules.db.base import getDB

from .dependencies import getUser

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup(Response: JSONResponse,
           userdata: UserSchemaAdd,
           db: Session = Depends(getDB)):
  if(getUser(userdata.email, db)):
    raise HTTPException(status_code=405, detail="User already exists")
  
  user = dbRegisterUser(db, userdata)
  if user:
    return JSONResponse({"message": "User created successfully"}, status_code=201)
  return HTTPException(status_code=400, detail="User creation failed")

@router.post("/login")
async def login(formData: OAuth2PasswordRequestForm = Depends()):
  grant_type = formData.grant_type
  if grant_type == "password":
    username = formData.username
    password = formData.password

    user = getUser(username)
    if not user or user.password != password:
      return InvalidCredentialsException
    
    # 로그인 세션 생성
    # response = RedirectResponse(url="/protected", status_code=302)
    response = JSONResponse({"message": "Login successful"}, status_code=302)
    Depends().set_cookie(response, Depends().create_access_token(data={'sub':user["username"]},
                                                                       scopes=['read:protected', 'write:protected']))
    return response
  else:
    raise JSONResponse({"message": "Invalid grant type"}, status_code=400)

@router.post("/find")
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