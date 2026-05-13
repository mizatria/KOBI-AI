from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
from starlette.requests import Request
from starlette.responses import RedirectResponse

from database import SessionLocal
from models import Customer, Order
from routers.authentication import get_current_vendor, templates

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

class CustomerUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str

class CustomerCreateRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str


@router.get("/")
async def list_customers_page(request: Request, vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    customers = db.query(Customer).all()
    return templates.TemplateResponse(
        request=request,
        name="customers.html",
        context={"customers": customers, "vendor": vendor}
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_customer(vendor: vendor_dependency, db: db_dependency, request: CustomerCreateRequest):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    customer = Customer(
        first_name=request.first_name,
        last_name=request.last_name,
        phone_number=request.phone_number
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", status_code=status.HTTP_200_OK)
async def update_customer(vendor: vendor_dependency, db: db_dependency, update: CustomerUpdateRequest, customer_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Müşteri bulunamadı")
    customer.first_name   = update.first_name
    customer.last_name    = update.last_name
    customer.phone_number = update.phone_number
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(vendor: vendor_dependency, db: db_dependency, customer_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Müşteri bulunamadı")
    db.delete(customer)
    db.commit()
    return {"message": "Müşteri silindi"}


@router.get("/{customer_id}/orders")
async def get_customer_orders(customer_id: int, vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    return db.query(Order).filter(
        Order.customer_id == customer_id,
        Order.vendor_id == vendor.get('id')
    ).all()