from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Vendor
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime,timedelta,timezone
from typing import Annotated
import os
from dotenv import load_dotenv
from fastapi import Request
from fastapi.templating import Jinja2Templates


router=APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

templates = Jinja2Templates(directory="templates")

bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

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

oauth2_bearer=OAuth2PasswordBearer(tokenUrl="auth/login")


def create_access_token(username:str,user_id:str,expires_delta:timedelta):
    payload={"sub":username,"id":user_id}
    expires=datetime.now(timezone.utc)+expires_delta
    payload.update({"exp":expires})
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

async def get_current_vendor(token:Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username=payload.get("sub")
        vendor_id=payload.get("id")
        if username is None or vendor_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Username or ID is invalid")
        return {"username":username,"id":vendor_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token is invalid")

@router.get("/register")
async def render_register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request})
@router.get("/login")
async def render_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request})

@router.post("/login", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: db_dependency):
    vendor = db.query(Vendor).filter(Vendor.username == form_data.username).first()
    if not vendor or not bcrypt_context.verify(form_data.password, vendor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or Password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        vendor.username,
        str(vendor.id),
        token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def create_vendor(create_vendor:CreateVendorRequest,db:db_dependency):
    db_user = db.query(Vendor).filter(
        (Vendor.username == create_vendor.username) |
        (Vendor.email == create_vendor.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or Email already registered")
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