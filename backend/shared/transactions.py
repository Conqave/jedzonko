from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class TransactionManager(ABC):
    @abstractmethod
    def atomic(self) -> AbstractContextManager[None]:
        raise NotImplementedError
