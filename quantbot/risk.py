from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import math

from .portfolio import Portfolio


@dataclass
class RiskManager:
    max_leverage: float = 1.0
    risk_per_trade: float = 0.005  # 0.5% of equity at risk per trade
    max_drawdown: float = 0.2  # 20%
    volatility_lookback: int = 200
    vol_ewm_alpha: float = 0.05

    # Internal state
    _ewm_var: Optional[float] = field(default=None, init=False)
    _last_price: Optional[float] = field(default=None, init=False)

    def update_volatility(self, price: float) -> None:
        if self._last_price is None:
            self._last_price = price
            return
        ret = (price / self._last_price) - 1.0
        self._last_price = price
        if self._ewm_var is None:
            self._ewm_var = ret * ret
        else:
            self._ewm_var = (1 - self.vol_ewm_alpha) * self._ewm_var + self.vol_ewm_alpha * (ret * ret)

    def get_annualized_vol(self) -> float:
        if self._ewm_var is None:
            return 0.0
        per_step_vol = math.sqrt(max(self._ewm_var, 1e-12))
        annualized_vol = per_step_vol * math.sqrt(252 * 6.5 * 60 * 60)
        return float(annualized_vol)

    def check_drawdown(self, portfolio: Portfolio) -> bool:
        return portfolio.max_drawdown >= self.max_drawdown

    def target_shares(self, *,
                      portfolio: Portfolio,
                      price: float,
                      signal_direction: int,
                      signal_strength: float) -> int:
        if signal_direction == 0:
            return 0

        equity = portfolio.equity
        if equity <= 0:
            return 0

        vol = self.get_annualized_vol()
        if vol <= 0:
            dollar_at_risk = equity * self.risk_per_trade
            stop_distance = price * 0.01  # 1%
            qty = int(max(dollar_at_risk / max(stop_distance, 1e-6), 1))
        else:
            stop_distance = price * min(0.02, 0.5 * vol / 100.0)
            dollar_at_risk = equity * self.risk_per_trade * max(min(signal_strength, 1.0), 0.1)
            qty = int(max(dollar_at_risk / max(stop_distance, 1e-6), 1))

        max_notional = equity * self.max_leverage
        max_qty_by_leverage = int(max_notional / price)
        qty = int(min(qty, max_qty_by_leverage))

        return int(signal_direction * qty)