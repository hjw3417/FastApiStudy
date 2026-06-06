import uvicorn

from fastapi import FastAPI
from user.interface.controller.user_controller import router as user_router
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from containers import container

app = FastAPI()
app.container = container
app.include_router(user_router)

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