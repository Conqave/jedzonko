from abc import ABC, abstractmethod


class ProductTagRepository(ABC):
    @abstractmethod
    def create_tag(self, product_id: int, name: str, source: str) -> None:
        raise NotImplementedError
