from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from trading_bot.broker.paper import PaperBroker
from trading_bot.config import BotConfig, StrategyMode, SubMode
from trading_bot.core.events import PriceTick
from trading_bot.core.models import CycleStats
from trading_bot.strategies.cdm import CDMStrategy
from trading_bot.strategies.wdm import WDMStrategy
from trading_bot.strategies.zrm import ZRMStrategy
from trading_bot.strategies.izrm import IZRMStrategy


@dataclass
class EngineResult:
    cycles: List[CycleStats]


class TradingEngine:
    def __init__(self, cfg: BotConfig, starting_equity: float = 100_000.0):
        self.cfg = cfg
        self.broker = PaperBroker()
        self.starting_equity = starting_equity
        self.equity = starting_equity

        self.cycles: List[CycleStats] = []
        self._cycle_id = 0
        self._active_cycle: Optional[CycleStats] = None

        self.strategies = self._build_strategies()
        self._sequential_chosen: Optional[str] = None
        self._initial_anchor: Optional[float] = None

    def _build_strategies(self) -> Dict[str, object]:
        strategies: Dict[str, object] = {}
        if self.cfg.cdm and self.cfg.cdm.enabled:
            strategies["CDM"] = CDMStrategy(self.cfg.cdm, self.broker)
        if self.cfg.wdm and self.cfg.wdm.enabled:
            strategies["WDM"] = WDMStrategy(self.cfg.wdm, self.broker)
        if self.cfg.zrm and self.cfg.zrm.enabled:
            strategies["ZRM"] = ZRMStrategy(self.cfg.zrm, self.broker)
        if self.cfg.izrm and self.cfg.izrm.enabled:
            strategies["IZRM"] = IZRMStrategy(self.cfg.izrm, self.broker)
        return strategies

    def _start_cycle_if_needed(self, tick: PriceTick):
        if self._active_cycle is not None:
            return
        self._cycle_id += 1
        self._active_cycle = CycleStats(
            cycle_id=self._cycle_id,
            symbol=tick.symbol,
            start_ts=tick.timestamp.isoformat(),
            start_equity=self.equity,
            end_equity=self.equity,
        )
        self._active_cycle.peak_equity = self.equity
        self._active_cycle.trough_equity = self.equity
        self._sequential_chosen = None
        self._initial_anchor = None

    def _close_cycle(self, tick: PriceTick, realized_pnl: float):
        if self._active_cycle is None:
            return
        self.equity += realized_pnl
        self._active_cycle.realized_pnl += realized_pnl
        self._active_cycle.end_equity = self.equity
        self._active_cycle.end_ts = tick.timestamp.isoformat()
        self.cycles.append(self._active_cycle)
        self._active_cycle = None

    def _update_drawdown(self, mark_price: float):
        unrealized = 0.0
        for pos in self.broker.positions.values():
            unrealized += pos.unrealized_pnl(mark_price)
        if self._active_cycle:
            self._active_cycle.update_equity(self.equity + unrealized)

    def _route_single(self, name: str, tick: PriceTick):
        strategy = self.strategies.get(name)
        if not strategy:
            return
        realized = strategy.on_price(tick)
        if realized is not None:
            self._close_cycle(tick, realized_pnl=realized)

    def _route_parallel(self, tick: PriceTick):
        any_closed = False
        total_realized = 0.0
        for strat in self.strategies.values():
            realized = strat.on_price(tick)
            if realized is not None:
                any_closed = True
                total_realized += realized
        if any_closed:
            self._close_cycle(tick, realized_pnl=total_realized)

    def _route_sequential(self, tick: PriceTick):
        primary = self.cfg.primary_strategy
        if self._initial_anchor is None:
            self._initial_anchor = tick.price

        if self._sequential_chosen is None:
            distance = self.cfg.second_order_distance_pct
            up = tick.price >= self._initial_anchor * (1 + distance)
            down = tick.price <= self._initial_anchor * (1 - distance)

            if up and "WDM" in self.strategies:
                self._sequential_chosen = "WDM"
            elif down and "CDM" in self.strategies:
                self._sequential_chosen = "CDM"
            else:
                strat = self.strategies.get(primary)
                if strat:
                    realized = strat.on_price(tick)
                    if realized is not None:
                        self._close_cycle(tick, realized_pnl=realized)
                return

        strat = self.strategies.get(self._sequential_chosen)
        if strat:
            realized = strat.on_price(tick)
            if realized is not None:
                self._close_cycle(tick, realized_pnl=realized)

    def on_tick(self, tick: PriceTick):
        self._start_cycle_if_needed(tick)
        self._update_drawdown(tick.price)

        if self.cfg.mode in (
            StrategyMode.CDM_ONLY,
            StrategyMode.WDM_ONLY,
            StrategyMode.ZRM_ONLY,
            StrategyMode.IZRM_ONLY,
        ):
            name = self.cfg.mode.value.replace("_ONLY", "")
            self._route_single(name, tick)
            return

        if self.cfg.submode == SubMode.PARALLEL:
            self._route_parallel(tick)
        else:
            self._route_sequential(tick)

    def run_backtest(self, ticks: List[PriceTick]) -> EngineResult:
        for tick in ticks:
            self.on_tick(tick)
            if not self.cfg.shared.continue_trading and self.cycles:
                break
        return EngineResult(cycles=self.cycles)
