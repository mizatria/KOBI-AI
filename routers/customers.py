from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
from database import SessionLocal
from models import Customer, Order
from routers.authentication import get_current_vendor

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
vendor_dependency = Annotated[dict, Depends(get_current_vendor)]

@router.get("/{customer_id}/orders")
async def get_customer_orders(customer_id: int, vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Vendor not provided")
    return db.query(Order).filter(
        Order.customer_id == customer_id,
        Order.vendor_id == vendor.get('id')
    ).all()

@router.get("/", status_code=status.HTTP_200_OK)
async def list_customers(vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Vendor not provided")
    customer_ids = db.query(Order.customer_id).filter(Order.vendor_id == vendor.get('id')).distinct().all()
    customer_ids = [c[0] for c in customer_ids]
    return db.query(Customer).filter(Customer.id.in_(customer_ids)).all()