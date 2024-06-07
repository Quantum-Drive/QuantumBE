from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException

oauth2Scheme = OAuth2PasswordBearer(tokenUrl="/token")

class NotAuthenticatedException(Exception):
  def __init__(self):
    super().__init__("User is not authenticated")



def main():
  app = FastAPI()
  SECRET = "super-secret-key"
  loginManager = LoginManager(SECRET, '/auth/login', use_cookie=True, custom_exception=NotAuthenticatedException)
  
  def verifyToken(token: str = Depends(loginManager)):
    if not token or token == "null":
      raise NotAuthenticatedException
    return token

  @app.exception_handler(NotAuthenticatedException)
  def authExceptionHandler(request, exc):
    return RedirectResponse(url="/auth/login")

  @app.get("/token")
  def get_token():
    # Your code to retrieve and return the user's token here
    return {"token": "YOUR_TOKEN"}

if __name__ == "__main__":
  main()
  
  