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
        """유저의 노트 목록을 페이지네이션해서 조회한다.

        Returns:
            (전체 개수, 노트 리스트) 튜플
        """ 
        raise NotImplementedError
    
    @abstractmethod
    def find_by_id(self, user_id:str, id:str)-> Note:
        """유저 id로 노트 상세를 조회한다
        Returns:
            Note
        """
        raise NotImplementedError
    