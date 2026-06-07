from note.domain.note import Note
from note.domain.repository.note_repo import INoteRepository
from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from database import SessionLocal
from note.domain.note import Note as NoteVO
from note.domain.repository.note_repo import INoteRepository
from note.infra.db_models.note import Note, Tag
from utils.db_utils import row_to_dict


class NoteRepository(INoteRepository):
    def get_notes(
            self,
            user_id:str,
            page: int,
            items_per_page: int,
    )-> tuple[int,list[NoteVO]]:
        with SessionLocal() as db:
            query = (
                db.query(Note)
                .options(joinedload(Note.tags))
                .filter(Note.user_id == user_id)
            )

            total_count = query.count()
            notes = (
                query.offset((page-1) * items_per_page)
                .limit(items_per_page).all()
            )

        note_vos = [NoteVO(**row_to_dict(note)) for note in notes]

        return total_count, note_vos