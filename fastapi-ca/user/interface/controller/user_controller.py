from fastapi import APIRouter
from pydantic import BaseModel

from user.application.user_service import UserService

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

router = APIRouter(prefix="/users")

@router.post("", status_code=201)
def create_user(user: UserCreate):
    user_service = UserService()
    created_user = user_service.create_user(user.name, user.email, user.password)
    return created_user


