from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from datetime import datetime, timezone


class Side(Enum):
    BUY = auto()
    SELL = auto()


@dataclass
class PriceEvent:
    symbol: str
    timestamp: datetime
    price: float


@dataclass
class SignalEvent:
    symbol: str
    timestamp: datetime
    direction: int  # -1 short, 0 flat, 1 long
    strength: float  # 0..1 suggested aggressiveness
    reference_price: Optional[float] = None


@dataclass
class OrderEvent:
    symbol: str
    timestamp: datetime
    side: Side
    quantity: int
    order_type: str = "market"


@dataclass
class FillEvent:
    symbol: str
    timestamp: datetime
    side: Side
    quantity: int
    price: float
    commission: float
    slippage: float


@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    equity: float
    cash: float
    position_qty: int
    position_avg_price: float


def now_utc() -> datetime:
    return datetime.now(timezone.utc)