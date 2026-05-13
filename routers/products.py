import markdown
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from database import SessionLocal
from models import Product
from routers.authentication import get_current_vendor, templates
from bs4 import BeautifulSoup
from typing import Annotated
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

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
    supplier_id:int | None=None

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency=Annotated[Session,Depends(get_db)]
vendor_dependency=Annotated[dict,Depends(get_current_vendor)]


@router.get("/")
async def list_products_page(request: Request, vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    products = db.query(Product).filter(Product.vendor_id == vendor.get('id')).all()

    from models import Supplier
    suppliers = db.query(Supplier).filter(Supplier.vendor_id == vendor.get('id')).all()

    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "products": products,
            "suppliers": suppliers,
            "vendor": vendor
        }
    )

@router.get("/store", status_code=status.HTTP_200_OK)
async def list_store_products(db: db_dependency, category: str = None):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    return query.all()

@router.get("/store/categories", status_code=status.HTTP_200_OK)
async def list_categories(db: db_dependency):
    categories = db.query(Product.category).distinct().all()
    return [c[0] for c in categories if c[0]]

@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_product(vendor:vendor_dependency,db:db_dependency,create_product_request:CreateProductRequest):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    product=Product(**create_product_request.dict(),vendor_id=vendor.get('id'))
    product.description = await create_description_with_gemini(
        product.name,
        product.description or "",
        str(product.unit))
    db.add(product)
    db.commit()

@router.delete("/{product_id}",status_code=status.HTTP_200_OK)
async def delete_product(vendor:vendor_dependency,db:db_dependency,product_id:int=Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    product=db.query(Product).filter(Product.id == product_id).filter(Product.vendor_id == vendor.get('id')).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.query(Product).filter(Product.id == product_id).delete()
    db.commit()

@router.put("/{product_id}",status_code=status.HTTP_200_OK)
async def update_product(vendor:vendor_dependency,db:db_dependency, product_request:CreateProductRequest, product_id:int=Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    product=db.query(Product).filter(Product.id == product_id).filter(Product.vendor_id==vendor.get('id')).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    description_changed = product.description != product_request.description
    name_changed = product.name != product_request.name
    if description_changed or name_changed:
        product.description = await create_description_with_gemini(
            product_request.name,
            product_request.description,
            str(product_request.unit)
        )
    product.name = product_request.name
    product.price = product_request.price
    product.unit = product_request.unit
    product.category = product_request.category
    product.stock = product_request.stock
    product.min_stock_limit = product_request.min_stock_limit
    product.supplier_id = product_request.supplier_id

    db.add(product)
    db.commit()

def markdown_to_text(markdown_string:str):
    html=markdown.markdown(markdown_string)
    soup=BeautifulSoup(html,'html.parser')
    text=soup.get_text()
    return text


async def create_description_with_gemini(product_name: str, product_description: str, product_unit: str):
    load_dotenv()

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.environ.get("GROQ_API_KEY")
    )
    prompt = (
        f"Sen profesyonel bir e-ticaret içerik yazarı ve pazarlama uzmanısın. "
        f"Aşağıdaki bilgileri kullanarak müşteriyi satın almaya ikna edecek, samimi ve iştah açıcı "
        f"en fazla 5 cümlelik bir ürün açıklaması yaz.\n\n"
        f"Ürün Adı: {product_name}\n"
        f"Satıcı Notu: {product_description}\n"
        f"Birim: {product_unit}\n\n"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return markdown_to_text(response.content)