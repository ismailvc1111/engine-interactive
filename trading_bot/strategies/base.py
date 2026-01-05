from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from trading_bot.broker.base import Broker
from trading_bot.config import MartingaleConfig
from trading_bot.core.events import PriceTick
from trading_bot.core.models import Position


@dataclass
class StrategyState:
    active: bool = False
    current_leg: int = 0
    anchor_price: Optional[float] = None
    trailing_stop: Optional[float] = None
    realized_pnl: float = 0.0


class Strategy(ABC):
    name: str

    def __init__(self, cfg: MartingaleConfig, broker: Broker):
        self.cfg = cfg
        self.broker = broker
        self.state = StrategyState()
        self.position = Position(symbol=cfg.symbol)

    @abstractmethod
    def on_price(self, tick: PriceTick) -> Optional[float]:
        """Handle a price tick. Return realized PnL when a cycle closes."""
        ...

    def is_enabled(self) -> bool:
        return bool(self.cfg and self.cfg.enabled)

    def _reset(self):
        self.position.legs.clear()
        self.state = StrategyState()
