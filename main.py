from fastapi import FastAPI, Request
from starlette import status
import models
from database import engine
from routers.authentication import router as auth_router

app=FastAPI()
app.include_router(auth_router)
models.Base.metadata.create_all(bind=engine)