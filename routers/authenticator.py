from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup():
  # Implement your signup logic here
  pass

@router.post("/login")
async def login(formData: OAuth2PasswordRequestForm = router.dependencies[0]):
  grant_type = formData.grant_type
  if grant_type == "password":
    username = formData.username
    password = formData.password

    user = load_user(username)
    if not user or user["password"] != password:
      raise HTTPException(
        status_code=401,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
      )
    
    # 로그인 세션 생성
    # response = RedirectResponse(url="/protected", status_code=302)
    response = JSONResponse({"message": "Login successful"})
    loginManager.set_cookie(response, loginManager.create_access_token(data={'sub':user["username"]},
                                                                       scopes=['read:protected', 'write:protected']))
    return response
  else:
    raise NotAuthenticatedException

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