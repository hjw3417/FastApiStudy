from fastapi import APIRouter
from pydantic import BaseModel
from dataclasses import asdict
from dependency_injector.wiring import inject, Provide
from datetime import datetime
from fastapi import APIRouter, Depends
from common.auth import CurrentUser, get_current_user
from note.application.note_service import NoteService
from containers import Container
from typing import Annotated

router = APIRouter(prefix="/notes")

CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
NoteServiceDep = Annotated[NoteService, Depends(Provide[Container.note_service])]

class NoteResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    memo_date: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class GetNoteResponse(BaseModel):
    total_count: int
    page: int
    notes: list[NoteResponse]

@router.get("", response_model=GetNoteResponse)
@inject
def get_notes(
    current_user: CurrentUserDep,
    note_service: NoteServiceDep,
    page: int=1,
    items_per_page: int=10,
):
    total_count, notes = note_service.get_notes(
        user_id=current_user.id,
        page=page,
        items_per_page=items_per_page,
    )

    res_notes = []
    for note in notes:
        note_dict = asdict(note)
        note_dict.update({"tags": [tag.name for tag in note.tags]})
        res_notes.append(note_dict)

    return{
        "total_count": total_count,
        "page": page,
        "notes": res_notes,
    }

@router.get("/{id}", response_model=NoteResponse)
@inject
def find_by_id(
    current_user: CurrentUserDep,
    note_service: NoteServiceDep,
    id: str,
):
    note = note_service.find_by_id(current_user.id, id)

    note_dict = asdict(note)
    note_dict.update({
        "tags":[tag.name for tag in note.tags]
        })
    return note_dict

@router.get("/tags/{tag_name}", response_model=GetNoteResponse)
@inject
def get_notes_by_tag_name(
    current_user: CurrentUserDep,s
    note_service: NoteServiceDep,
    tag_name:str,
    page: int=1,
    items_per_page: int=10,
):
    total_count, notes = note_service.get_notes_by_tag_name(
    user_id=current_user.id,
    tag_name=tag_name,
    page=page,
    items_per_page=items_per_page,
    )

    res_notes = []
    for note in notes:
        note_dict = asdict(note)
        note_dict.update({"tags": [tag.name for tag in note.tags]})
        res_notes.append(note_dict)

    return{
        "total_count": total_count,
        "page": page,
        "notes": res_notes,
    }