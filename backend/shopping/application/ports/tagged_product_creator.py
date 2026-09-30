from abc import ABC, abstractmethod
from datetime import datetime


class TaggedProductCreator(ABC):
    @abstractmethod
    def create_tagged_product(
        self,
        user_id: int,
        household_id: int,
        ingredient_id: int,
        name: str,
        unit_code: str,
        now: datetime,
    ) -> int:
        raise NotImplementedError
