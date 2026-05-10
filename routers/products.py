import markdown
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Product
from routers.authentication import get_current_vendor
from bs4 import BeautifulSoup
from typing import Annotated
import os
from dotenv import load_dotenv
from fastapi import Request
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage



router = APIRouter(
    prefix="/products",
    tags=["products"]
)

class CreateProductRequest(BaseModel):
    name:str
    description:str
    price:float
    unit:str
    category:str
    stock:float
    min_stock_limit:float
    supplier_id:int

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency=Annotated[Session,Depends(get_db)]
vendor_dependency=Annotated[dict,Depends(get_current_vendor)]


@router.post("/products/create",status_code=status.HTTP_201_CREATED)
async def create_product(vendor:vendor_dependency,db:db_dependency,create_product_request:CreateProductRequest):
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Vendor not provided")
    product=Product(**create_product_request.dict(),vendor_id=vendor.get('id'))
    product.description = await create_description_with_gemini(
        product.name,
        product.description or "",
        str(product.unit))
    db.add(product)
    db.commit()

def markdown_to_text(markdown_string:str):
    html=markdown.markdown(markdown_string)
    soup=BeautifulSoup(html,'html.parser')
    text=soup.get_text()
    return text

async def create_description_with_gemini(product_name:str,product_description:str,product_unit:str):
    load_dotenv()
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
    llm=ChatGoogleGenerativeAI(model="gemini-pro")
    prompt = (
        f"Sen profesyonel bir e-ticaret içerik yazarı ve pazarlama uzmanısın. "
        f"Aşağıdaki bilgileri kullanarak müşteriyi satın almaya ikna edecek, samimi ve iştah açıcı "
        f"en fazla 5 cümlelik bir ürün açıklaması yaz.\n\n"
        f"Ürün Adı: {product_name}\n"
        f"Satıcı Notu: {product_description}\n"
        f"Birim: {product_unit}\n\n"
    )
    response = await llm.invoke([HumanMessage(content=prompt)])
    return markdown_to_text(response.content)