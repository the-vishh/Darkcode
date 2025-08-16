from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import timedelta
from typing import AsyncIterator, Optional

import logging

from .events import PriceEvent, now_utc


logger = logging.getLogger(__name__)


@dataclass
class BaseFeed:
    symbol: str

    async def stream(self) -> AsyncIterator[PriceEvent]:  # pragma: no cover - to be implemented by subclasses
        raise NotImplementedError


@dataclass
class SyntheticFeed(BaseFeed):
    interval_seconds: float = 0.5
    duration_seconds: int = 60
    seed: Optional[int] = 42

    async def stream(self) -> AsyncIterator[PriceEvent]:
        if self.seed is not None:
            random.seed(self.seed)

        steps = int(self.duration_seconds / self.interval_seconds)
        timestamp = now_utc()
        price = 100.0
        mean_price = 100.0
        phi = 0.98  # OU mean reversion speed
        sigma = 0.2  # base noise per step

        for _ in range(steps):
            # occasional jumps
            jump = random.gauss(0.0, 2.0) if random.random() < 0.01 else 0.0
            # Ornstein-Uhlenbeck update
            noise = random.gauss(0.0, sigma)
            price = mean_price + phi * (price - mean_price) + noise + jump

            timestamp = timestamp + timedelta(seconds=self.interval_seconds)
            event = PriceEvent(symbol=self.symbol, timestamp=timestamp, price=float(price))
            yield event
            await asyncio.sleep(self.interval_seconds)


@dataclass
class YFinancePollingFeed(BaseFeed):
    interval_seconds: float = 2.0
    duration_seconds: int = 300

    async def stream(self) -> AsyncIterator[PriceEvent]:
        try:
            import yfinance as yf  # type: ignore
        except Exception:  # noqa: BLE001
            logger.warning("yfinance is not installed; YFinancePollingFeed is unavailable")
            return

        start = now_utc()
        last_price: Optional[float] = None
        while (now_utc() - start).total_seconds() <= self.duration_seconds:
            try:
                ticker = yf.Ticker(self.symbol)
                info = ticker.fast_info
                price = float(info.last_price)
                if price and price != last_price:
                    last_price = price
                    yield PriceEvent(symbol=self.symbol, timestamp=now_utc(), price=price)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"yfinance polling error: {e}")

            await asyncio.sleep(self.interval_seconds)