import asyncio
import json
import logging
import websocket
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from threading import Thread
import queue
import time

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    bid: float = None
    ask: float = None
    high: float = None
    low: float = None
    open: float = None

class RealTimeDataFeed:
    """Real-time market data feed with WebSocket connection"""
    
    def __init__(self, symbols: List[str], api_key: str = None):
        self.symbols = symbols
        self.api_key = api_key
        self.data_queue = queue.Queue()
        self.subscribers = []
        self.ws = None
        self.running = False
        self.logger = logging.getLogger(__name__)
        
    def subscribe(self, callback: Callable[[MarketData], None]):
        """Subscribe to market data updates"""
        self.subscribers.append(callback)
        
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Parse different message types
            if isinstance(data, list):
                for item in data:
                    self._process_data_item(item)
            else:
                self._process_data_item(data)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            
    def _process_data_item(self, item: dict):
        """Process individual data item"""
        try:
            if item.get('T') == 't':  # Trade data
                market_data = MarketData(
                    symbol=item.get('S'),
                    timestamp=datetime.fromtimestamp(item.get('t', 0) / 1000),
                    price=float(item.get('p', 0)),
                    volume=int(item.get('s', 0))
                )
                
                # Notify all subscribers
                for callback in self.subscribers:
                    callback(market_data)
                    
        except Exception as e:
            self.logger.error(f"Error processing data item: {e}")
            
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        self.logger.error(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.logger.info("WebSocket connection closed")
        
    def _on_open(self, ws):
        """Handle WebSocket open"""
        self.logger.info("WebSocket connection opened")
        
        # Subscribe to symbols
        auth_message = {
            "action": "auth",
            "key": self.api_key,
            "secret": ""
        }
        ws.send(json.dumps(auth_message))
        
        # Subscribe to trades
        subscribe_message = {
            "action": "subscribe",
            "trades": self.symbols
        }
        ws.send(json.dumps(subscribe_message))
        
    def start(self):
        """Start the real-time data feed"""
        self.running = True
        
        # For demo purposes, we'll use Yahoo Finance with simulation
        # In production, replace with actual WebSocket connection
        self._start_simulation_feed()
        
    def _start_simulation_feed(self):
        """Start simulation feed using Yahoo Finance data"""
        def simulation_worker():
            while self.running:
                for symbol in self.symbols:
                    try:
                        ticker = yf.Ticker(symbol)
                        data = ticker.history(period="1d", interval="1m")
                        
                        if not data.empty:
                            latest = data.iloc[-1]
                            market_data = MarketData(
                                symbol=symbol,
                                timestamp=datetime.now(),
                                price=float(latest['Close']),
                                volume=int(latest['Volume']),
                                high=float(latest['High']),
                                low=float(latest['Low']),
                                open=float(latest['Open'])
                            )
                            
                            # Notify subscribers
                            for callback in self.subscribers:
                                callback(market_data)
                                
                    except Exception as e:
                        self.logger.error(f"Error fetching data for {symbol}: {e}")
                        
                time.sleep(1)  # Update every second
                
        thread = Thread(target=simulation_worker, daemon=True)
        thread.start()
        
    def stop(self):
        """Stop the data feed"""
        self.running = False
        if self.ws:
            self.ws.close()

class HistoricalDataProvider:
    """Provider for historical market data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_historical_data(self, symbol: str, period: str = "1y", 
                          interval: str = "1d") -> pd.DataFrame:
        """Get historical data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            # Add technical indicators
            data = self._add_technical_indicators(data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
            
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical indicators to historical data"""
        # Moving averages
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['EMA_20'] = data['Close'].ewm(span=20).mean()
        
        # Volatility
        data['Returns'] = data['Close'].pct_change()
        data['Volatility'] = data['Returns'].rolling(window=20).std()
        
        # Price ranges
        data['HL_Range'] = data['High'] - data['Low']
        data['OC_Range'] = abs(data['Open'] - data['Close'])
        
        return data
        
    def get_multiple_symbols(self, symbols: List[str], 
                           period: str = "1y") -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            results[symbol] = self.get_historical_data(symbol, period)
            
        return results

class DataProcessor:
    """Process and clean market data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess market data"""
        # Remove outliers using IQR method
        Q1 = data['Close'].quantile(0.25)
        Q3 = data['Close'].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outlier bounds
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Filter outliers
        data = data[(data['Close'] >= lower_bound) & (data['Close'] <= upper_bound)]
        
        # Forward fill missing values
        data = data.fillna(method='ffill')
        
        # Remove any remaining NaN values
        data = data.dropna()
        
        return data
        
    def normalize_data(self, data: pd.DataFrame, 
                      columns: List[str] = None) -> pd.DataFrame:
        """Normalize data using z-score normalization"""
        if columns is None:
            columns = ['Close', 'Volume', 'High', 'Low', 'Open']
            
        normalized_data = data.copy()
        
        for col in columns:
            if col in data.columns:
                mean = data[col].mean()
                std = data[col].std()
                normalized_data[f'{col}_normalized'] = (data[col] - mean) / std
                
        return normalized_data
        
    def calculate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced features for ML models"""
        features = data.copy()
        
        # Price-based features
        features['price_change'] = features['Close'].pct_change()
        features['price_acceleration'] = features['price_change'].diff()
        
        # Volume-based features
        features['volume_change'] = features['Volume'].pct_change()
        features['price_volume'] = features['Close'] * features['Volume']
        
        # Volatility features
        features['intraday_return'] = (features['Close'] - features['Open']) / features['Open']
        features['overnight_return'] = (features['Open'] - features['Close'].shift(1)) / features['Close'].shift(1)
        
        # Momentum features
        for period in [5, 10, 20]:
            features[f'momentum_{period}'] = features['Close'] / features['Close'].shift(period) - 1
            
        # Mean reversion features
        for period in [5, 10, 20]:
            features[f'mean_reversion_{period}'] = (features['Close'] - features['Close'].rolling(period).mean()) / features['Close'].rolling(period).std()
            
        return features

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Initialize data feed
    data_feed = RealTimeDataFeed(symbols)
    
    def on_data(market_data: MarketData):
        print(f"{market_data.symbol}: ${market_data.price:.2f} at {market_data.timestamp}")
    
    data_feed.subscribe(on_data)
    data_feed.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        data_feed.stop()