# QuantBot: Real-time Quant Trading Framework (Starter)

QuantBot is a modular, event-driven starter framework for building real-time quant trading systems with advanced math-based signal generation, risk management, and execution. It ships with a synthetic real-time feed so you can run it immediately without credentials. Swap in live feeds/brokers later.

## Quickstart

1) Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Run in synthetic live mode (no credentials needed)

```bash
python run_live.py --mode synthetic --symbol TEST --duration 60 --starting-cash 100000
```

3) Optional: Run with yfinance polling (minute-ish updates; not true RT)

```bash
python run_live.py --mode yfinance --symbol AAPL --duration 300 --starting-cash 100000 --poll-interval 5
```

## Modules
- `quantbot.feed`: Real-time data feeds (Synthetic, YFinance).
- `quantbot.strategy`: Advanced signal generation (Kalman filter trend + regime switching).
- `quantbot.risk`: Risk management (volatility targeting, drawdown guard, position sizing).
- `quantbot.execution`: Simple execution router (market orders; easy to extend to TWAP/VWAP/POV).
- `quantbot.broker`: Simulated broker with slippage & fees; plug in a real broker later.
- `quantbot.portfolio`: Portfolio tracking with PnL and NAV.
- `quantbot.engine`: Event loop tying everything together.

## Notes
- This starter focuses on correctness and clarity, not raw performance. It is ready for extension and experimentation.
- For real brokerage integration (e.g., Alpaca, IBKR), create new connectors in `quantbot.broker` and `quantbot.feed`.
