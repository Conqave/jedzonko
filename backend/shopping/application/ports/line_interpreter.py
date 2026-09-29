from abc import ABC, abstractmethod
from datetime import datetime

from shopping.domain.line_meaning import LineMeaning


class LineInterpreter(ABC):
    @abstractmethod
    def interpret(self, texts: tuple[str, ...], now: datetime) -> dict[str, LineMeaning]:
        raise NotImplementedError
