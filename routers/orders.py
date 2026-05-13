import os
import urllib.parse
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Path
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import RedirectResponse

from database import SessionLocal
from models import Customer, Order, Product, Vendor, Supplier
from routers.authentication import get_current_vendor, templates
from enum import Enum

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
vendor_dependency = Annotated[dict, Depends(get_current_vendor)]

class CreateOrderRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    product_id: int
    quantity: float

class OrderStatus(str, Enum):
    received  = "Alındı"
    shipped = "Kargoya Verildi"
    completed = "Tamamlandı"

class OrderUpdateRequest(BaseModel):
    customer_id: int
    product_id: int
    quantity: float
    status: str

async def generate_whatsapp_message(product_name: str, current_stock: float, unit: str, supplier_name: str) -> str:
    load_dotenv()
    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
    prompt = (
        f"Sen bir KOBİ sahibisin ve tedarikçine stok yenileme mesajı yazacaksın."
        f"Kısa, samimi ve profesyonel bir Whatsapp mesajı yaz."
        f"Türkçe yaz.\n\n"
        f"Ürün: {product_name}\n"
        f"Mevcut Stok: {current_stock} {unit}\n"
        f"Tedarikçi: {supplier_name}\n"
        f"Sadece mesajı yaz, başka bir şey ekleme."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


@router.get("/", status_code=status.HTTP_200_OK)
async def list_orders_page(request: Request, vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    orders = db.query(Order).filter(Order.vendor_id == vendor.get('id')).order_by(Order.created_at.desc()).all()
    products = db.query(Product).filter(Product.vendor_id == vendor.get('id')).all()

    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={
            "orders": orders,
            "products": products,
            "vendor": vendor
        }
    )


@router.post("/manual", status_code=status.HTTP_201_CREATED)
async def create_manual_order(vendor: vendor_dependency, db: db_dependency, order_request: CreateOrderRequest):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    vendor_id = vendor.get('id')
    customer = db.query(Customer).filter(Customer.phone_number == order_request.phone_number).first()
    if customer is None:
        customer = Customer(
            first_name=order_request.first_name,
            last_name=order_request.last_name,
            phone_number=order_request.phone_number
        )
        db.add(customer)
        db.flush()
    product = db.query(Product).filter(Product.id == order_request.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    if product.stock < order_request.quantity:
        raise HTTPException(status_code=400, detail="Yetersiz stok")
    order = Order(
        customer_id=customer.id,
        vendor_id=vendor_id,
        product_id=order_request.product_id,
        quantity=order_request.quantity,
        price=product.price * order_request.quantity,
        status="Alındı"
    )
    db.add(order)
    product.stock -= order_request.quantity
    db.commit()
    if product.stock <= product.min_stock_limit:
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        if supplier:
            supplier_name = f"{supplier.first_name} {supplier.last_name}"
            ai_message = await generate_whatsapp_message(product.name, product.stock, product.unit, supplier_name)
            phone = supplier.phone_number.replace(" ", "").replace("+", "")
            wa_link = f"https://wa.me/{phone}?text={urllib.parse.quote(ai_message)}"
            return {"message": "Sipariş oluşturuldu", "order_id": order.id, "stock_alert": {"warning": f"{product.name} stoğu kritik seviyede!", "current_stock": product.stock, "ai_message": ai_message, "wa_link": wa_link}}
    return {"message": "Sipariş oluşturuldu", "order_id": order.id}


@router.post("/store", status_code=status.HTTP_201_CREATED)
async def create_store_order(db: db_dependency, order_request: CreateOrderRequest):
    product = db.query(Product).filter(Product.id == order_request.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    vendor_id = product.vendor_id
    if product.stock < order_request.quantity:
        raise HTTPException(status_code=400, detail="Yetersiz stok")
    customer = db.query(Customer).filter(Customer.phone_number == order_request.phone_number).first()
    if customer is None:
        customer = Customer(
            first_name=order_request.first_name,
            last_name=order_request.last_name,
            phone_number=order_request.phone_number
        )
        db.add(customer)
        db.flush()
    order = Order(
        customer_id=customer.id,
        vendor_id=vendor_id,
        product_id=order_request.product_id,
        quantity=order_request.quantity,
        price=product.price * order_request.quantity,
        status="Alındı"
    )
    db.add(order)
    product.stock -= order_request.quantity
    db.commit()
    if product.stock <= product.min_stock_limit:
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        if supplier:
            supplier_name = f"{supplier.first_name} {supplier.last_name}"
            ai_message = await generate_whatsapp_message(product.name, product.stock, product.unit, supplier_name)
            phone = supplier.phone_number.replace(" ", "").replace("+", "")
            wa_link = f"https://wa.me/{phone}?text={urllib.parse.quote(ai_message)}"
            return {"message": "Sipariş oluşturuldu", "order_id": order.id, "stock_alert": {"warning": f"{product.name} stoğu kritik seviyede!", "current_stock": product.stock, "ai_message": ai_message, "wa_link": wa_link}}
    return {"message": "Sipariş oluşturuldu", "order_id": order.id}


@router.get("/{order_id}", status_code=status.HTTP_200_OK)
async def get_detailed_order(vendor: vendor_dependency, db: db_dependency, order_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    order = db.query(Order).filter(Order.id == order_id, Order.vendor_id == vendor.get('id')).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return order


@router.put("/{order_id}", status_code=status.HTTP_200_OK)
async def update_order(vendor: vendor_dependency, db: db_dependency, order_update: OrderUpdateRequest, order_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    order = db.query(Order).filter(Order.id == order_id, Order.vendor_id == vendor.get('id')).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    order.customer_id = order_update.customer_id
    order.product_id  = order_update.product_id
    order.quantity    = order_update.quantity
    order.status      = order_update.status
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(vendor: vendor_dependency, db: db_dependency, order_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    order = db.query(Order).filter(Order.id == order_id, Order.vendor_id == vendor.get('id')).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(order)
    db.commit()
    return {"message": "Sipariş silindi"}