from database import Base
from sqlalchemy import Column,Integer,String,Boolean,ForeignKey,Float

class Vendor(Base):
    __tablename__='vendors'
    id=Column(Integer,primary_key=True)
    email=Column(String, unique=True)
    username=Column(String,unique=True)
    first_name=Column(String)
    last_name=Column(String)
    company_name=Column(String)
    hashed_password=Column(String)

class Product(Base):
    __tablename__='products'
    id=Column(Integer,primary_key=True)
    name=Column(String)
    description=Column(String)
    price=Column(Float)
    stock=Column(Float)
    vendor_id=Column(Integer,ForeignKey('vendors.id'))
    min_stock_limit=Column(Float)
    unit=Column(String)
    category=Column(String)
    supplier_id=Column(Integer,ForeignKey('suppliers.id'))

class Supplier(Base):
    __tablename__='suppliers'
    id=Column(Integer,primary_key=True)
    first_name=Column(String)
    last_name=Column(String)
    company_name=Column(String)
    phone_number=Column(String)
    email=Column(String)
    vendor_id=Column(Integer,ForeignKey('vendors.id'))
