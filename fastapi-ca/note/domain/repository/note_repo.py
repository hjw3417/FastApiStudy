from abc import ABCMeta, abstractmethod
from note.domain.note import Note

class INoteRepository(metaclass=ABCMeta):
    @abstractmethod
    def get_notes(
        self,
        user_id: str,
        page: int,
        items_per_page: int,
    ) -> tuple[int, list[Note]]:
        raise NotImplementedError