from fastapi import APIRouter, Depends, HTTPException,Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Vendor
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import jwt, JWTError
from starlette.responses import RedirectResponse
from datetime import datetime,timedelta,timezone
from typing import Annotated
import os
from dotenv import load_dotenv

router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

class CreateVendorRequest(BaseModel):
    email:str
    username:str
    first_name:str
    last_name:str
    company_name:str
    password:str

class Token(BaseModel):
    access_token:str
    token_type:str

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency=Annotated[Session,Depends(get_db)]

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def create_vendor(create_vendor:CreateVendorRequest,db:db_dependency):
    hashed_pass = bcrypt_context.hash(create_vendor.password)
    vendor=Vendor(
        email=create_vendor.email,
        username=create_vendor.username,
        first_name=create_vendor.first_name,
        last_name=create_vendor.last_name,
        company_name=create_vendor.company_name,
        hashed_password=hashed_pass,
    )
    db.add(vendor)
    db.commit()