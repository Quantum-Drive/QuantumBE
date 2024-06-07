from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from fastapi.responses import FileResponse

router = APIRouter(prefix="/auth")

@router.post("/signup")
def signup():
  # Implement your signup logic here
  pass

@router.post("/login")
def login():
  # Implement your login logic here
  pass

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