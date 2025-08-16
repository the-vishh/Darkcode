from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import math

from .events import SignalEvent


@dataclass
class KalmanTrendFilter:
    # 2D state: [level, trend]
    process_var_level: float = 1e-4
    process_var_trend: float = 1e-6
    measurement_var: float = 1e-2

    # Internal state
    x_level: Optional[float] = field(default=None, init=False)
    x_trend: Optional[float] = field(default=None, init=False)
    P00: Optional[float] = field(default=None, init=False)
    P01: Optional[float] = field(default=None, init=False)
    P10: Optional[float] = field(default=None, init=False)
    P11: Optional[float] = field(default=None, init=False)

    def update(self, price: float) -> tuple[float, float]:
        q0 = self.process_var_level
        q1 = self.process_var_trend
        r = self.measurement_var

        if self.x_level is None:
            self.x_level = price
            self.x_trend = 0.0
            self.P00 = 1.0
            self.P01 = 0.0
            self.P10 = 0.0
            self.P11 = 1.0

        # Predict step
        x0_pred = self.x_level + self.x_trend
        x1_pred = self.x_trend

        # P_pred = F P F^T + Q with F=[[1,1],[0,1]] and Q=diag(q0,q1)
        FP00 = self.P00 + self.P10
        FP01 = self.P01 + self.P11
        FP10 = self.P10
        FP11 = self.P11

        P00_pred = FP00 + FP01 + q0
        P01_pred = FP01
        P10_pred = FP10 + FP11
        P11_pred = FP11 + q1

        # Update step
        y = price - x0_pred
        S = P00_pred + r
        if S <= 1e-12:
            S = 1e-12
        K0 = P00_pred / S
        K1 = P10_pred / S

        self.x_level = x0_pred + K0 * y
        self.x_trend = x1_pred + K1 * y

        self.P00 = (1.0 - K0) * P00_pred
        self.P01 = (1.0 - K0) * P01_pred
        self.P10 = P10_pred - K1 * P00_pred
        self.P11 = P11_pred - K1 * P01_pred

        return float(self.x_level), float(self.x_trend)


@dataclass
class AdvancedStrategy:
    symbol: str
    z_ewm_alpha: float = 0.05
    z_entry: float = 2.0
    z_exit: float = 0.5
    trend_threshold: float = 0.001  # per tick trend threshold

    # Internal state
    kf: KalmanTrendFilter = field(default_factory=KalmanTrendFilter)
    _resid_mean: Optional[float] = field(default=None, init=False)
    _resid_var: Optional[float] = field(default=None, init=False)

    def _update_residual_stats(self, resid: float) -> tuple[float, float, float]:
        if self._resid_mean is None:
            self._resid_mean = resid
            self._resid_var = resid * resid
        else:
            self._resid_mean = (1 - self.z_ewm_alpha) * self._resid_mean + self.z_ewm_alpha * resid
            dev = resid - self._resid_mean
            self._resid_var = (1 - self.z_ewm_alpha) * self._resid_var + self.z_ewm_alpha * (dev * dev)
        std = math.sqrt(max(self._resid_var or 0.0, 1e-12))
        z = (resid - (self._resid_mean or 0.0)) / max(std, 1e-6)
        return z, (self._resid_mean or 0.0), std

    def on_price(self, *, timestamp: datetime, price: float) -> SignalEvent:
        level, trend = self.kf.update(price)
        resid = price - level
        z, _, _ = self._update_residual_stats(resid)

        # Regime: if residual z is very high frequently, treat as mean-reverting; else trend
        mr_bias = min(abs(z) / max(self.z_entry, 1e-6), 1.0)
        trend_bias = min(abs(trend) / max(self.trend_threshold, 1e-6), 1.0)

        use_mr = mr_bias > trend_bias

        direction = 0
        strength = 0.0

        if use_mr:
            # Mean reversion: fade residual extremes
            if z > self.z_entry:
                direction = -1
                strength = min((z - self.z_entry) / max(self.z_entry, 1e-6), 1.0)
            elif z < -self.z_entry:
                direction = 1
                strength = min((-self.z_entry - z) / max(self.z_entry, 1e-6), 1.0)
            elif abs(z) < self.z_exit:
                direction = 0
                strength = 0.0
        else:
            # Trend following: trade with Kalman trend
            if trend > self.trend_threshold:
                direction = 1
                strength = min(trend / (10 * self.trend_threshold), 1.0)
            elif trend < -self.trend_threshold:
                direction = -1
                strength = min(-trend / (10 * self.trend_threshold), 1.0)

        strength = max(0.0, min(1.0, strength))
        return SignalEvent(
            symbol=self.symbol,
            timestamp=timestamp,
            direction=direction,
            strength=strength,
            reference_price=price,
        )