from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from trading_bot.core.models import Side


@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    size: float
    price: float
    ts: str


class Broker(ABC):
    @abstractmethod
    def place_order(self, symbol: str, side: Side, size: float, price: Optional[float], ts: str) -> Fill:
        ...

    @abstractmethod
    def close_position(self, symbol: str, ts: str, price: float) -> float:
        """Return realized PnL for the closed position."""
        ...
