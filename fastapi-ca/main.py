import uvicorn

from fastapi import FastAPI
from user.interface.controller.user_controller import router as user_router

app = FastAPI()
app.include_router(user_router)

@app.get("/")
def hello():
    return {"Hello": "FastAPI"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", reload=True)