import uvicorn

from fastapi import FastAPI
from user.interface.controller.user_controller import router as user_router
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from containers import Container
from example.ch06_02.sync_ex import router as sync_ex_routers

app = FastAPI()
app.container = Container()
app.include_router(user_router)
app.include_router(sync_ex_routers)

@app.get("/")
def hello():
    return {"Hello": "FastAPI"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=exc.errors()
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", reload=True)