import os
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TradingConfig:
    """Configuration for the quantitative trading system"""
    
    # API Keys and Credentials
    ALPACA_API_KEY: str = os.getenv('ALPACA_API_KEY', '')
    ALPACA_SECRET_KEY: str = os.getenv('ALPACA_SECRET_KEY', '')
    ALPACA_BASE_URL: str = 'https://paper-api.alpaca.markets'  # Paper trading
    
    # Trading Parameters
    INITIAL_CAPITAL: float = 100000.0
    MAX_POSITION_SIZE: float = 0.1  # 10% of portfolio per position
    MAX_DAILY_LOSS: float = 0.02    # 2% max daily loss
    STOP_LOSS_PCT: float = 0.02     # 2% stop loss
    TAKE_PROFIT_PCT: float = 0.06   # 6% take profit
    
    # Risk Management
    VAR_CONFIDENCE: float = 0.95    # 95% confidence for VaR
    MAX_DRAWDOWN: float = 0.15      # 15% max drawdown
    POSITION_SIZING_METHOD: str = 'kelly'  # 'fixed', 'kelly', 'optimal_f'
    
    # Data Feed
    DATA_SOURCE: str = 'alpaca'     # 'alpaca', 'yahoo', 'polygon'
    WEBSOCKET_URL: str = 'wss://stream.data.alpaca.markets/v2/iex'
    
    # Model Parameters
    LOOKBACK_PERIOD: int = 252      # 1 year of trading days
    REBALANCE_FREQUENCY: str = 'daily'  # 'minute', 'hourly', 'daily'
    
    # Technical Indicators
    RSI_PERIOD: int = 14
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD: float = 2.0
    
    # Machine Learning
    FEATURE_WINDOW: int = 60        # Features lookback window
    PREDICTION_HORIZON: int = 5     # Predict next 5 periods
    MODEL_RETRAIN_FREQ: int = 30    # Retrain every 30 days
    
    # Symbols to trade
    SYMBOLS: List[str] = None
    
    def __post_init__(self):
        if self.SYMBOLS is None:
            self.SYMBOLS = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
                'META', 'NVDA', 'NFLX', 'AMD', 'CRM'
            ]

# Global config instance
config = TradingConfig()