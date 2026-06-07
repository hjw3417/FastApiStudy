from ulid import ULID
from note.domain.note import Note
from note.domain.repository.note_repo import INoteRepository

class NoteService:
    def __init__(
            self,
            note_repo: INoteRepository
    ):
        self.note_repo = note_repo
        self.ulid = ULID()

    def get_notes(
            self,
            user_id:str,
            page:int,
            items_per_page:int,
    )->tuple[int, list[Note]]:
        return self.note_repo.get_notes(
            user_id=user_id,
            page=page,
            items_per_page=items_per_page,
        )
    
    def find_by_id(
            self,
            user_id: str,
            id: str,
    ) -> Note:
        return self.note_repo.find_by_id(
            user_id = user_id,
            id=id,
        )