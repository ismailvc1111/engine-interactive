from __future__ import annotations

from typing import Optional

from trading_bot.config import ZoneConfig
from trading_bot.core.events import PriceTick
from trading_bot.core.models import Leg, Side
from trading_bot.core.utils import pct
from trading_bot.strategies.base import Strategy


class IZRMStrategy(Strategy):
    name = "IZRM"

    def __init__(self, cfg: ZoneConfig, broker):
        super().__init__(cfg, broker)
        self.cfg: ZoneConfig = cfg
        self._breakout_side: Optional[Side] = None

    def _bounds(self):
        width = pct(self.cfg.zone_width_pct)
        center = self.cfg.zone_center_price
        return (center * (1 - width), center * (1 + width))

    def _should_enter(self, tick: PriceTick) -> bool:
        if self.state.active:
            return False
        lower, upper = self._bounds()
        if tick.price > upper:
            self._breakout_side = Side.SELL
            return True
        if tick.price < lower:
            self._breakout_side = Side.BUY
            return True
        return False

    def _enter(self, tick: PriceTick):
        side = self._breakout_side or self.cfg.initial_side
        size0 = self.cfg.order_sizes[0]
        self.broker.place_order(self.cfg.symbol, side, size0, tick.price, tick.timestamp.isoformat())
        self.position.legs.append(Leg(side, size0, tick.price, tick.timestamp.isoformat()))
        self.state.active = True
        self.state.current_leg = 1

    def _maybe_add_leg(self, tick: PriceTick):
        if not self.state.active:
            return
        if self.state.current_leg >= self.cfg.max_orders:
            return
        leg_index = self.state.current_leg
        if leg_index >= len(self.cfg.order_distances_pct) or leg_index >= len(self.cfg.order_sizes):
            return

        lower, upper = self._bounds()
        touched_zone = tick.price <= lower or tick.price >= upper
        if not touched_zone:
            return

        if not self.cfg.hold_previous and self.position.legs:
            realized = self.broker.close_position(self.cfg.symbol, tick.timestamp.isoformat(), tick.price)
            self.state.realized_pnl += realized
            self.position.legs.clear()
            self.state.current_leg = 0

        side = self.position.direction()
        size = self.cfg.order_sizes[leg_index]
        self.broker.place_order(self.cfg.symbol, side, size, tick.price, tick.timestamp.isoformat())
        self.position.legs.append(Leg(side, size, tick.price, tick.timestamp.isoformat()))
        self.state.current_leg += 1

    def _maybe_exit(self, tick: PriceTick) -> bool:
        lower, upper = self._bounds()
        if not (lower <= tick.price <= upper):
            return False
        if not self.position.legs:
            return False

        last_idx = max(0, self.state.current_leg - 1)
        stop_loss = pct(self.cfg.order_sls_pct[min(last_idx, len(self.cfg.order_sls_pct) - 1)])
        avg = self.position.avg_entry_price()
        side = self.position.direction()

        if side == Side.BUY:
            return tick.price <= avg * (1 - stop_loss)
        return tick.price >= avg * (1 + stop_loss)

    def _close_cycle(self, tick: PriceTick) -> float:
        realized = self.broker.close_position(self.cfg.symbol, tick.timestamp.isoformat(), tick.price)
        total_realized = realized + self.state.realized_pnl
        self._reset()
        self._breakout_side = None
        return total_realized

    def on_price(self, tick: PriceTick) -> Optional[float]:
        if not self.state.active:
            if self._should_enter(tick):
                self._enter(tick)
            return None

        self._maybe_add_leg(tick)

        if self._maybe_exit(tick):
            return self._close_cycle(tick)

        return None
