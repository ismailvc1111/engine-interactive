from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class StrategyMode(str, Enum):
    CDM_ONLY = "CDM_ONLY"
    WDM_ONLY = "WDM_ONLY"
    ZRM_ONLY = "ZRM_ONLY"
    IZRM_ONLY = "IZRM_ONLY"
    MULTIPLE = "MULTIPLE"


class SubMode(str, Enum):
    PARALLEL = "PARALLEL"
    SEQUENTIAL = "SEQUENTIAL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class SharedSettings:
    continue_trading: bool = True
    pre_after_hours: bool = False
    repeat_on_close: bool = True
    backtest_report: bool = True
    order_type: OrderType = OrderType.MARKET

    mm_reinvest_on: bool = False
    growth_threshold: float = 10_000.0
    increase_value_pct: float = 0.0
    progressive_reinvestment_step_pct: float = 0.0


@dataclass(frozen=True)
class MartingaleConfig:
    enabled: bool
    symbol: str
    capital_allocation_pct: float

    initial_side: Side
    price_trigger: Optional[float]

    max_orders: int
    hold_previous: bool

    order_distances_pct: List[float]
    order_sizes: List[float]
    order_tps_pct: List[float]
    order_sls_pct: List[float]

    trailing_enabled: bool = False
    trailing_first_move_pct: float = 0.0
    trailing_step_pct: float = 0.0


@dataclass(frozen=True)
class ZoneConfig(MartingaleConfig):
    zone_center_price: float = 0.0
    zone_width_pct: float = 0.01


@dataclass(frozen=True)
class BotConfig:
    shared: SharedSettings
    mode: StrategyMode
    submode: SubMode = SubMode.PARALLEL

    primary_strategy: str = "CDM"
    second_order_distance_pct: float = 0.01

    cdm: Optional[MartingaleConfig] = None
    wdm: Optional[MartingaleConfig] = None
    zrm: Optional[ZoneConfig] = None
    izrm: Optional[ZoneConfig] = None
