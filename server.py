import pytz

import fastapi
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_login.exceptions import InvalidCredentialsException
from starlette.middleware.sessions import SessionMiddleware

from apscheduler.schedulers.background import BackgroundScheduler
from periodicTasks import sqliteJobs

from routers import authenticator
from routers import fileManager
from routers.dependencies import loginManager, SECRET, verifyToken

app = FastAPI()

# app.add_middleware(SessionMiddleware, secret_key=SECRET)
app.include_router(authenticator.router)
app.include_router(fileManager.router, dependencies=[Depends(loginManager)])

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



@app.get("/token")
async def getToken(token: str = Depends(loginManager)):
  return {"token": token}

# 보호된 엔드포인트
@app.get("/protected")
async def protected(token: str = Depends(loginManager)):
  return {"message": f"Hello, {token.username}!"}

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("server:app", host="0.0.0.0", port=5300, reload=True)
  
  