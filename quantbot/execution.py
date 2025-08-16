from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .events import OrderEvent, Side


@dataclass
class ExecutionRouter:
    def target_to_order(self, *, symbol: str, timestamp: datetime, current_qty: int, target_qty: int) -> OrderEvent | None:
        delta = target_qty - current_qty
        if delta == 0:
            return None
        side = Side.BUY if delta > 0 else Side.SELL
        return OrderEvent(symbol=symbol, timestamp=timestamp, side=side, quantity=abs(delta), order_type="market")