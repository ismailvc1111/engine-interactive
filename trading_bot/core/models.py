from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Leg:
    side: Side
    size: float
    entry_price: float
    entry_ts: str


@dataclass
class Position:
    symbol: str
    legs: List[Leg] = field(default_factory=list)

    def total_size(self) -> float:
        size = 0.0
        for leg in self.legs:
            size += leg.size if leg.side == Side.BUY else -leg.size
        return size

    def avg_entry_price(self) -> float:
        total = sum(abs(l.size) for l in self.legs)
        if total == 0:
            return 0.0
        return sum(abs(l.size) * l.entry_price for l in self.legs) / total

    def direction(self) -> Side:
        if not self.legs:
            return Side.BUY
        return self.legs[0].side

    def unrealized_pnl(self, mark_price: float) -> float:
        pnl = 0.0
        for leg in self.legs:
            if leg.side == Side.BUY:
                pnl += (mark_price - leg.entry_price) * leg.size
            else:
                pnl += (leg.entry_price - mark_price) * leg.size
        return pnl


@dataclass
class CycleStats:
    cycle_id: int
    symbol: str
    start_ts: str
    end_ts: Optional[str] = None

    start_equity: float = 0.0
    end_equity: float = 0.0

    realized_pnl: float = 0.0
    max_drawdown: float = 0.0
    peak_equity: float = 0.0
    trough_equity: float = 0.0

    num_orders: int = 0

    def update_equity(self, equity: float):
        if self.peak_equity == 0.0:
            self.peak_equity = equity
            self.trough_equity = equity
            self.max_drawdown = 0.0
            return

        if equity > self.peak_equity:
            self.peak_equity = equity
        if equity < self.trough_equity:
            self.trough_equity = equity

        drawdown = self.peak_equity - equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
