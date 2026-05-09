from database import Base
from sqlalchemy import Column,Integer,String,Boolean,ForeignKey

class Vendor(Base):
    __tablename__='vendors'
    id=Column(Integer,primary_key=True)
    email=Column(String, unique=True)
    username=Column(String,unique=True)
    first_name=Column(String)
    last_name=Column(String)
    company_name=Column(String)
    hashed_password=Column(String)

