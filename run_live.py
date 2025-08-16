import argparse
import asyncio
import logging

from quantbot.feed import SyntheticFeed, YFinancePollingFeed
from quantbot.strategy import AdvancedStrategy
from quantbot.risk import RiskManager
from quantbot.broker import SimulatedBroker
from quantbot.portfolio import Portfolio
from quantbot.engine import Engine


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QuantBot in live/sim mode")
    parser.add_argument("--mode", choices=["synthetic", "yfinance"], default="synthetic")
    parser.add_argument("--symbol", type=str, default="TEST")
    parser.add_argument("--duration", type=int, default=60, help="Duration seconds to run")
    parser.add_argument("--starting-cash", type=float, default=100_000)
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between polls for yfinance mode")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.mode == "synthetic":
        feed = SyntheticFeed(symbol=args.symbol, interval_seconds=0.5, duration_seconds=args.duration)
    else:
        feed = YFinancePollingFeed(symbol=args.symbol, interval_seconds=args.poll_interval, duration_seconds=args.duration)

    strategy = AdvancedStrategy(symbol=args.symbol)
    risk = RiskManager(max_leverage=1.0, risk_per_trade=0.005, max_drawdown=0.2)
    broker = SimulatedBroker(starting_cash=args.starting_cash)
    portfolio = Portfolio(starting_cash=args.starting_cash)

    engine = Engine(feed=feed, strategy=strategy, risk=risk, broker=broker, portfolio=portfolio)

    logger.info(f"Starting engine with mode={args.mode}, symbol={args.symbol}")
    await engine.run()
    logger.info("Engine finished")


if __name__ == "__main__":
    asyncio.run(main())