from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from containers import Container
from user.application.user_service import UserService
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from common.auth import CurrentUser, get_current_user
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=32)
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=8, max_length=32)

class UpdateUserBody(BaseModel):
    name: str | None = None
    password: str | None = None

class UserResponse(BaseModel):
    id:str
    name: str
    email: str
    create_at: datetime
    update_at: datetime

class GetUsersResponse(BaseModel):
    total_count: int
    page: int
    users: list[UserResponse]




router = APIRouter(prefix="/users")

@router.post("", status_code=201)
@inject
def create_user(
    user: UserCreate,
    user_service: UserService = Depends(Provide[Container.user_service])
    # user_service: UserService = Depends(Provide["user_service"])
)->UserResponse:
    created_user = user_service.create_user(user.name, user.email, user.password)
    return created_user

@router.put("", response_model = UserResponse)
@inject
def update_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    body: UpdateUserBody,
    user_service: UserService = Depends(Provide[Container.user_service])
):
    updated_user = user_service.update_user(
        user_id=current_user.id,
        name=body.name,
        password=body.password
    )
    return updated_user

@router.get("")
@inject
def get_users(
    page: int = 1,
    items_per_page:int = 10,
    user_service: UserService = Depends(Provide[Container.user_service])
) -> GetUsersResponse:
    total_count, users = user_service.get_users(page, items_per_page)
    return {
        "total_count": total_count,
        "page": page,
        "users": users,
    }

@router.delete("", status_code=204)
@inject
def delete_user(
    user_id: str,
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    # TODO: 다른 유저를 삭제할 수 없도록 토큰에서 유저 아이디를 구한다.

    user_service.delete_user(user_id)

@router.post("/login")
@inject
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    access_token = user_service.login(
        email=form_data.username,
        password=form_data.password,
    )

    return {"access_token": access_token, "token_type": "bearer"}
