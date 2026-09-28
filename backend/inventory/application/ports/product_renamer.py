from abc import ABC, abstractmethod


class ProductRenamer(ABC):
    @abstractmethod
    def set_product_name(self, user_id: int, product_id: int, name: str) -> None:
        raise NotImplementedError
