from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PriceTick:
    symbol: str
    price: float
    timestamp: datetime
