from abc import ABC, abstractmethod


class PromotionAccess(ABC):
    @abstractmethod
    def can_view_promotions(self, user_id: int) -> bool:
        raise NotImplementedError
