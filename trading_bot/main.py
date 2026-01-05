from __future__ import annotations

import math
from datetime import datetime, timedelta

from trading_bot.config import (
    BotConfig,
    MartingaleConfig,
    OrderType,
    SharedSettings,
    Side,
    StrategyMode,
    SubMode,
    ZoneConfig,
)
from trading_bot.core.engine import TradingEngine
from trading_bot.core.events import PriceTick


def make_sine_ticks(symbol: str, start_price: float = 100.0, count: int = 800) -> list[PriceTick]:
    start = datetime(2025, 1, 1, 9, 30)
    ticks = []
    for i in range(count):
        price = start_price * (1 + 0.02 * math.sin(i / 30.0)) * (1 + 0.00005 * i)
        ticks.append(PriceTick(symbol=symbol, price=float(price), timestamp=start + timedelta(minutes=i)))
    return ticks


def main():
    shared = SharedSettings(
        continue_trading=True,
        repeat_on_close=True,
        order_type=OrderType.MARKET,
        backtest_report=True,
    )

    cdm = MartingaleConfig(
        enabled=True,
        symbol="SPY",
        capital_allocation_pct=0.5,
        initial_side=Side.BUY,
        price_trigger=None,
        max_orders=5,
        hold_previous=True,
        order_distances_pct=[0.0, 0.005, 0.0075, 0.01, 0.0125],
        order_sizes=[10, 15, 22, 33, 50],
        order_tps_pct=[0.004, 0.004, 0.004, 0.004, 0.004],
        order_sls_pct=[0.01, 0.01, 0.01, 0.01, 0.01],
        trailing_enabled=False,
    )

    wdm = MartingaleConfig(
        enabled=True,
        symbol="SPY",
        capital_allocation_pct=0.5,
        initial_side=Side.BUY,
        price_trigger=None,
        max_orders=5,
        hold_previous=True,
        order_distances_pct=[0.0, 0.005, 0.0075, 0.01, 0.0125],
        order_sizes=[10, 15, 22, 33, 50],
        order_tps_pct=[0.004, 0.004, 0.004, 0.004, 0.004],
        order_sls_pct=[0.006, 0.006, 0.006, 0.006, 0.006],
        trailing_enabled=False,
    )

    cfg = BotConfig(
        shared=shared,
        mode=StrategyMode.MULTIPLE,
        submode=SubMode.SEQUENTIAL,
        primary_strategy="CDM",
        second_order_distance_pct=0.005,
        cdm=cdm,
        wdm=wdm,
        zrm=None,
        izrm=None,
    )

    ticks = make_sine_ticks("SPY", 100.0, 800)
    engine = TradingEngine(cfg, starting_equity=100_000.0)
    result = engine.run_backtest(ticks)

    print(f"Cycles: {len(result.cycles)}")
    if result.cycles:
        profits = [c.realized_pnl for c in result.cycles]
        max_dd = [c.max_drawdown for c in result.cycles]
        print(f"Avg PnL/cycle: {sum(profits)/len(profits):.2f}")
        print(f"Max DD (avg): {sum(max_dd)/len(max_dd):.2f}")
        for cycle in result.cycles[:5]:
            print(
                f"Cycle {cycle.cycle_id} | start {cycle.start_ts} | end {cycle.end_ts} | "
                f"pnl {cycle.realized_pnl:.2f} | dd {cycle.max_drawdown:.2f}"
            )


if __name__ == "__main__":
    main()
