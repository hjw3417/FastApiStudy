from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Annotated
from dependency_injector.wiring import inject, Provide
from containers import Container
from user.application.user_service import UserService

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

router = APIRouter(prefix="/users")

@router.post("", status_code=201)
@inject
def create_user(
    user: UserCreate,
    user_service: UserService = Depends(Provide[Container.user_service])
    # user_service: UserService = Depends(Provide["user_service"])
):
    created_user = user_service.create_user(user.name, user.email, user.password)
    return created_user


