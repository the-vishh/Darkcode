from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import logging

from .events import OrderEvent, FillEvent, Side


logger = logging.getLogger(__name__)


@dataclass
class SimulatedBroker:
    starting_cash: float
    fee_bps: float = 1.0  # 1 bps
    base_slippage_bps: float = 1.0  # base slippage per fill

    def submit_order(self, order: OrderEvent, reference_price: float) -> Optional[FillEvent]:
        if order.quantity <= 0:
            return None

        side_sign = 1 if order.side == Side.BUY else -1
        slippage = (self.base_slippage_bps / 10_000.0) * reference_price
        fill_price = reference_price + side_sign * slippage

        commission = (self.fee_bps / 10_000.0) * abs(order.quantity) * reference_price

        fill = FillEvent(
            symbol=order.symbol,
            timestamp=order.timestamp,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            slippage=abs(slippage),
        )
        logger.debug(
            f"Filled {order.side.name} {order.quantity} {order.symbol} @ {fill_price:.4f} (ref {reference_price:.4f}, comm {commission:.2f})"
        )
        return fill