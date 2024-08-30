import pytz
import jwt
from datetime import datetime, timedelta
from dateutil.parser import parse

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from apscheduler.schedulers.background import BackgroundScheduler
from periodicTasks import sqliteJobs

from routers import authenticator, profile, file, trashbin
from routers.dependencies import loginManager

origins = [
  "http://localhost:5300",
  "https://localhost:3000",
  "https://quantumdrive.vercel.app"
]

app = FastAPI()

app.include_router(authenticator.router)
app.include_router(profile.router, dependencies=[Depends(loginManager)])
app.include_router(file.router, dependencies=[Depends(loginManager)])
app.include_router(trashbin.router, dependencies=[Depends(loginManager)])

# @app.exception_handler(NotAuthenticatedException)
# def authExceptionHandler(request: Request, exc: NotAuthenticatedException):
#   return RedirectResponse(url="/auth/login")

krTZ = pytz.timezone('Asia/Seoul')
scheduler = BackgroundScheduler(timezone=krTZ)
scheduler.add_job(sqliteJobs.deleteExpiredCache, 'interval', minutes=1, timezone=krTZ)
scheduler.start()

@app.on_event("startup")
async def startup_event():
  pass

@app.on_event("shutdown")
async def shutdown_event():
  scheduler.shutdown()

# @app.middleware("https")
# @app.middleware("http")
# async def refreshSession(request: Request, call_next):
#   # if request.headers and request.headers.get("Authorization"):
#   if request.cookies and request.cookies.get("access-token"):
#     token = request.cookies.get("access-token")
#     #token = request.headers.get("Authorization")
    
#     # token = token.split(" ")[1]
#     # userID = loginManager._get_payload(token)
#     try:
#       tokenData = jwt.decode(token, SECRET, algorithms=["HS256"])
#       data = {key: value for key, value in tokenData.items() if key not in {"exp", "scopes"}}
#       accessToken = loginManager.create_access_token(data=data, scopes=tokenData["scopes"])
#     except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
#       del(request.cookies["access-token"])
#       accessToken = ""
    
#     response = await call_next(request)
#     # print(response)
#     if response.headers.get("Set-Cookie") and 'access-token="";' in response.headers.get("Set-Cookie"):
#       pass
#     elif accessToken:
#       response.set_cookie(key="access-token", value=accessToken, httponly=True, secure=True, samesite="None")
#       # response.set_cookie(key="access-token", value=accessToken)
#     else:
#       response.delete_cookie("access-token")
#     return response
#   else:
#     return await call_next(request)

app.add_middleware(CORSMiddleware,
                    allow_origins=origins,
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                    )

@app.get("/token")
async def refreshToken(user = Depends(loginManager)):
  accessToken = loginManager.create_access_token(data={'sub':user.email},
                                                  scopes=['read:protected', 'write:protected'])
  return JSONResponse({"access_token": accessToken, "token_type":"bearer"}, status_code=200)

# 보호된 엔드포인트
@app.get("/protected")
async def protected(token: str = Depends(loginManager)):
  return {"message": f"Hello, {token.username}!"}

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("server:app", host="0.0.0.0", port=5300, reload=True,
              ssl_keyfile="quantumdrive.com+4-key.pem", ssl_certfile="quantumdrive.com+4.pem")
  
  