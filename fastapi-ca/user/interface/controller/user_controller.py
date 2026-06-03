from fastapi import APIRouter
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

router = APIRouter(prefix="/users")

@router.post("", status_code=201)
def create_user(user: UserCreate):
    return user
