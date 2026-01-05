from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from trading_bot.broker.base import Broker, Fill
from trading_bot.core.models import Leg, Position, Side


@dataclass
class PaperBroker(Broker):
    positions: Dict[str, Position] = field(default_factory=dict)

    def place_order(self, symbol: str, side: Side, size: float, price: Optional[float], ts: str) -> Fill:
        if price is None:
            raise ValueError("PaperBroker requires a price for fills (provide tick price).")

        pos = self.positions.get(symbol)
        if pos is None:
            pos = Position(symbol=symbol)
            self.positions[symbol] = pos

        pos.legs.append(Leg(side=side, size=size, entry_price=price, entry_ts=ts))
        return Fill(symbol=symbol, side=side, size=size, price=price, ts=ts)

    def close_position(self, symbol: str, ts: str, price: float) -> float:
        pos = self.positions.get(symbol)
        if not pos or not pos.legs:
            return 0.0

        realized = pos.unrealized_pnl(price)
        pos.legs.clear()
        return realized
