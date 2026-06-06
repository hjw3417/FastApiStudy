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


class UserUpdate(BaseModel):
    name: str | None = None
    password: str | None = None

@router.put("/{user_id}")
@inject
def update_user(
    user_id: str,
    user: UserUpdate,
    user_service: UserService = Depends(Provide[Container.user_service])
):
    updated_user = user_service.update_user(
        user_id=user_id,
        name=user.name,
        password=user.password
    )
    return updated_user

@router.get("")
@inject
def get_users(
    user_service: UserService = Depends(Provide[Container.user_service])
):
    users = user_service.get_users()
    return {
        "users": users,
    }