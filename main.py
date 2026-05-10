from fastapi import FastAPI, Request
from starlette import status
from starlette.responses import RedirectResponse
import models
from database import engine
from routers.authentication import router as auth_router
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers.products import router as product_router
from routers.suppliers import router as supplier_router
from routers.customers import router as customer_router
from routers.orders import router as orders_router
app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
models.Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(supplier_router)
app.include_router(customer_router)
app.include_router(orders_router)

@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login",status_code=status.HTTP_302_FOUND)