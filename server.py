import fastapi
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_login.exceptions import InvalidCredentialsException
from starlette.middleware.sessions import SessionMiddleware

from routers import authenticator
from routers.dependencies import loginManager, SECRET, verifyToken

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET)
app.include_router(authenticator.router)

# @app.exception_handler(NotAuthenticatedException)
# def authExceptionHandler(request: Request, exc: NotAuthenticatedException):
#   return RedirectResponse(url="/auth/login")



# @app.post("/token")
# async def login(response: Response,
#                 userdata: dict = Depends(loginManager)):
#   user = 
#   return {"token": "YOUR_TOKEN"}

@app.get("/token")
async def getToken(token: str = Depends(loginManager)):
  return {"token": token}

# 보호된 엔드포인트
@app.get("/protected")
async def protected(token: str = Depends(verifyToken)):
  return {"message": f"Hello, {token.username}!"}

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("server:app", host="0.0.0.0", port=5300, reload=True)
  
  