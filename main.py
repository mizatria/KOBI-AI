from fastapi import FastAPI, Request
from starlette import status
from starlette.responses import RedirectResponse

import models
from database import engine
from routers.authentication import router as auth_router

app=FastAPI()
models.Base.metadata.create_all(bind=engine)
app.include_router(auth_router)

@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login",status_code=status.HTTP_302_FOUND)