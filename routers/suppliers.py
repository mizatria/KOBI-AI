from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from routers.authentication import get_current_vendor
from database import SessionLocal
from models import Supplier, Vendor

router=APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)

class CreateSupplierRequest(BaseModel):
    first_name: str
    last_name: str
    company_name: str
    phone_number: str
    email: str

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency=Annotated[Session,Depends(get_db)]
vendor_dependency=Annotated[dict,Depends(get_current_vendor)]

@router.get("/",status_code=status.HTTP_200_OK)
async def list_suppliers(vendor:vendor_dependency,db:db_dependency):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    return db.query(Supplier).filter(Supplier.vendor_id == vendor.get('id')).all()

@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_supplier(vendor:vendor_dependency,db:db_dependency,create_supplier_request:CreateSupplierRequest ):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    supplier=Supplier(**create_supplier_request.dict(),vendor_id=vendor.get('id'))
    db.add(supplier)
    db.commit()

@router.delete("/{supplier_id}",status_code=status.HTTP_200_OK)
async def delete_supplier(vendor:vendor_dependency,db:db_dependency,supplier_id:int=Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    supplier=db.query(Supplier).filter(Supplier.id == supplier_id).filter(Supplier.vendor_id==vendor.get('id')).first()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Supplier not found")
    db.query(Supplier).filter(Supplier.id == supplier_id).delete()
    db.commit()

@router.put("/{supplier_id}",status_code=status.HTTP_200_OK)
async def update_supplier(vendor:vendor_dependency,db:db_dependency, create_supplier_request:CreateSupplierRequest, supplier_id:int=Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    supplier=db.query(Supplier).filter(Supplier.id == supplier_id).filter(Supplier.vendor_id==vendor.get('id')).first()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    supplier.first_name = create_supplier_request.first_name
    supplier.last_name = create_supplier_request.last_name
    supplier.company_name = create_supplier_request.company_name
    supplier.phone_number = create_supplier_request.phone_number
    supplier.email = create_supplier_request.email

    db.add(supplier)
    db.commit()