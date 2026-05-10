from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
from pydantic import BaseModel
from database import SessionLocal
from models import Customer, Order, Product, Vendor
from routers.authentication import get_current_vendor
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
    vendor_id: int

class OrderStatus(str, Enum):
    received   = "Sipariş Alındı"
    preparing  = "Hazırlanıyor"
    shipped    = "Kargoya Verildi"

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(db: db_dependency, order_request: CreateOrderRequest):
    customer = db.query(Customer).filter(
        Customer.phone_number == order_request.phone_number
    ).first()
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
        vendor_id=order_request.vendor_id,
        product_id=order_request.product_id,
        quantity=order_request.quantity,
        price=product.price * order_request.quantity,
        status="pending"
    )
    db.add(order)
    product.stock -= order_request.quantity
    db.commit()
    return {"message": "Sipariş oluşturuldu", "order_id": order.id}

@router.get("/",status_code=status.HTTP_200_OK)
async def list_orders(vendor:vendor_dependency,db: db_dependency):
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Order).filter(Order.vendor_id == vendor.get('id')).all()

@router.get("/{order_id}",status_code=status.HTTP_200_OK)
async def get_detailed_order(vendor:vendor_dependency,db: db_dependency, order_id: int=Path(gt=1000)):
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    order= db.query(Order).filter(Order.id == order_id).filter(Order.vendor_id==vendor.get('id')).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return order

@router.put("/{order_id}",status_code=status.HTTP_200_OK)
async def update_order_status(vendor:vendor_dependency,db: db_dependency,status_update: OrderStatusUpdate, order_id: int=Path(gt=1000)):
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    order = db.query(Order).filter(Order.id == order_id).filter(Order.vendor_id == vendor.get('id')).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    order.status = status_update.status
    db.commit()
    db.refresh(order)
    return order

