from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .events import FillEvent


def sign(x: int) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


@dataclass
class Position:
    quantity: int = 0
    avg_price: float = 0.0


@dataclass
class Portfolio:
    starting_cash: float
    cash: float = field(init=False)
    positions: Dict[str, Position] = field(default_factory=dict)
    equity: float = field(init=False)
    nav_high: float = field(init=False)
    max_drawdown: float = field(default=0.0)

    def __post_init__(self) -> None:
        self.cash = self.starting_cash
        self.equity = self.starting_cash
        self.nav_high = self.starting_cash

    def update_with_fill(self, fill: FillEvent) -> None:
        pos = self.positions.setdefault(fill.symbol, Position())
        side_sign = 1 if fill.side.name == "BUY" else -1
        trade_qty = side_sign * fill.quantity
        trade_value = trade_qty * fill.price

        # Update average price on position changes
        new_qty = pos.quantity + trade_qty
        if new_qty == 0:
            pos.avg_price = 0.0
        elif pos.quantity == 0:
            pos.avg_price = fill.price
        elif sign(pos.quantity) == sign(new_qty):
            pos.avg_price = (pos.avg_price * abs(pos.quantity) + fill.price * abs(trade_qty)) / abs(new_qty)
        else:
            if sign(new_qty) == 0:
                pos.avg_price = 0.0

        pos.quantity = new_qty
        self.cash -= trade_value
        self.cash -= fill.commission

    def mark_to_market(self, prices: Dict[str, float]) -> None:
        position_value = 0.0
        for symbol, pos in self.positions.items():
            px = prices.get(symbol)
            if px is None:
                continue
            position_value += pos.quantity * px
        self.equity = self.cash + position_value
        self.nav_high = max(self.nav_high, self.equity)
        if self.nav_high > 0:
            dd = 1.0 - (self.equity / self.nav_high)
            self.max_drawdown = max(self.max_drawdown, dd)

    def get_position(self, symbol: str) -> Position:
        return self.positions.get(symbol, Position())