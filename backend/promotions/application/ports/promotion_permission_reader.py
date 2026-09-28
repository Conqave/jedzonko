from abc import ABC, abstractmethod


class PromotionPermissionReader(ABC):
    @abstractmethod
    def can_view_promotions(self, user_id: int) -> bool:
        raise NotImplementedError
