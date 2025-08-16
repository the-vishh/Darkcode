from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict

from .events import PriceEvent
from .feed import BaseFeed
from .strategy import AdvancedStrategy
from .risk import RiskManager
from .broker import SimulatedBroker
from .portfolio import Portfolio
from .execution import ExecutionRouter


logger = logging.getLogger(__name__)


@dataclass
class Engine:
    feed: BaseFeed
    strategy: AdvancedStrategy
    risk: RiskManager
    broker: SimulatedBroker
    portfolio: Portfolio

    async def run(self) -> None:
        router = ExecutionRouter()
        async for price_event in self.feed.stream():
            await self._on_price(price_event, router)

    async def _on_price(self, event: PriceEvent, router: ExecutionRouter) -> None:
        # Update risk vol estimator
        self.risk.update_volatility(event.price)

        # Mark portfolio to market
        self.portfolio.mark_to_market({event.symbol: event.price})

        # Stop if drawdown exceeded
        if self.risk.check_drawdown(self.portfolio):
            logger.warning(
                f"Max drawdown reached ({self.portfolio.max_drawdown:.2%}). Halting trading."
            )
            # Sleep a little to let feed finish gracefully
            await asyncio.sleep(0.1)
            raise SystemExit(0)

        # Strategy signal
        signal = self.strategy.on_price(timestamp=event.timestamp, price=event.price)

        # Convert signal to target position (shares)
        target_qty = self.risk.target_shares(
            portfolio=self.portfolio,
            price=event.price,
            signal_direction=signal.direction,
            signal_strength=signal.strength,
        )

        current_qty = self.portfolio.get_position(event.symbol).quantity
        order = router.target_to_order(
            symbol=event.symbol,
            timestamp=event.timestamp,
            current_qty=current_qty,
            target_qty=target_qty,
        )

        if order is None:
            return

        fill = self.broker.submit_order(order, reference_price=event.price)
        if fill is not None:
            self.portfolio.update_with_fill(fill)
            self.portfolio.mark_to_market({event.symbol: event.price})
            logger.info(
                f"{event.timestamp.isoformat()} {event.symbol} px={event.price:.4f} qty={self.portfolio.get_position(event.symbol).quantity} "
                f"equity={self.portfolio.equity:.2f} dd={self.portfolio.max_drawdown:.2%}"
            )