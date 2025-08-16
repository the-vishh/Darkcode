# Advanced Quantitative Trading System

A sophisticated quantitative trading system that operates on real-time stock prices using advanced mathematical models, machine learning algorithms, and comprehensive risk management.

## 🚀 Features

### Core Components

- **Real-time Data Feed**: WebSocket connections for live market data
- **Advanced Mathematical Models**: Black-Scholes, GARCH, Kalman filters, Mean Reversion, Jump Diffusion, Regime Switching
- **Multi-factor Signal Generation**: Technical indicators, custom indicators, and ML-based signals
- **Sophisticated Risk Management**: VaR, position sizing, drawdown control, portfolio risk metrics
- **Professional Execution Engine**: Smart order routing, execution algorithms (TWAP, VWAP, Implementation Shortfall)
- **Comprehensive Backtesting**: Performance metrics, Monte Carlo simulation, walk-forward analysis

### Mathematical Models

1. **Black-Scholes Model**: Option pricing and Greeks calculation
2. **GARCH Model**: Volatility forecasting and clustering analysis
3. **Kalman Filter**: State space modeling for pairs trading
4. **Mean Reversion Model**: Ornstein-Uhlenbeck process for mean reversion strategies
5. **Jump Diffusion Model**: Merton model for handling sudden price jumps
6. **Regime Switching Model**: Markov models for different market regimes

### Signal Generation

- **Technical Indicators**: RSI, MACD, Bollinger Bands, Stochastic, ATR, ADX, Williams %R, CCI, OBV
- **Custom Indicators**: Hurst Exponent, Fractal Dimension, Market Efficiency Ratio
- **Machine Learning**: Random Forest, Gradient Boosting, Logistic Regression, SVM
- **Signal Combination**: Weighted combination with confidence scoring

### Risk Management

- **Value at Risk (VaR)**: Historical, Parametric, Cornish-Fisher methods
- **Position Sizing**: Kelly Criterion, Optimal f, Volatility-adjusted sizing
- **Drawdown Control**: Real-time monitoring and limits
- **Portfolio Risk**: Concentration risk, correlation analysis

### Execution Features

- **Order Types**: Market, Limit, Stop, Stop-Limit, Trailing Stop
- **Execution Algorithms**: TWAP, VWAP, Implementation Shortfall
- **Smart Order Routing**: Optimal venue selection
- **Slippage Modeling**: Realistic transaction cost estimation

## 📦 Installation

### Prerequisites

- Python 3.8+
- TA-Lib (for technical indicators)
- Required Python packages (see requirements.txt)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd quantitative-trading-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install TA-Lib:
```bash
# On Ubuntu/Debian
sudo apt-get install libta-lib-dev

# On macOS
brew install ta-lib

# Then install Python wrapper
pip install TA-Lib
```

4. Configure API keys (create `.env` file):
```bash
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
```

## 🔧 Configuration

Edit `config.py` to customize trading parameters:

```python
# Trading Parameters
INITIAL_CAPITAL = 100000.0
MAX_POSITION_SIZE = 0.1  # 10% of portfolio per position
MAX_DAILY_LOSS = 0.02    # 2% max daily loss
STOP_LOSS_PCT = 0.02     # 2% stop loss
TAKE_PROFIT_PCT = 0.06   # 6% take profit

# Risk Management
VAR_CONFIDENCE = 0.95
MAX_DRAWDOWN = 0.15
POSITION_SIZING_METHOD = 'kelly'  # 'fixed', 'kelly', 'optimal_f'

# Symbols to trade
SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
```

## 🚀 Usage

### Running the System

The system supports three modes:

1. **Paper Trading Mode** (default):
```bash
python quant_trading_system.py paper
```

2. **Live Trading Mode**:
```bash
python quant_trading_system.py live
```

3. **Backtesting Mode**:
```bash
python quant_trading_system.py backtest
```

### Example Usage

```python
from quant_trading_system import QuantTradingSystem
from config import config

# Initialize system
trading_system = QuantTradingSystem(config, mode='paper')

# Start trading
trading_system.start()

# Get system status
status = trading_system.get_status()
print(f"Portfolio Value: ${status['portfolio_value']:,.2f}")
print(f"Active Positions: {len(status['positions'])}")

# Stop system
trading_system.stop()
```

## 📊 Components Documentation

### Data Feed (`data_feed.py`)

Handles real-time and historical data:

```python
from data_feed import RealTimeDataFeed, HistoricalDataProvider

# Real-time data
data_feed = RealTimeDataFeed(['AAPL', 'MSFT'])
data_feed.subscribe(callback_function)
data_feed.start()

# Historical data
provider = HistoricalDataProvider()
data = provider.get_historical_data('AAPL', period='1y')
```

### Mathematical Models (`mathematical_models.py`)

Advanced quantitative models:

```python
from mathematical_models import BlackScholesModel, GARCHModel

# Black-Scholes option pricing
bs = BlackScholesModel()
call_price = bs.call_price(S=100, K=105, T=0.25, r=0.05, sigma=0.2)

# GARCH volatility modeling
garch = GARCHModel()
garch.fit(returns)
vol_forecast = garch.forecast(horizon=5)
```

### Signal Generation (`signal_generation.py`)

Multi-factor signal generation:

```python
from signal_generation import SignalGenerator

signal_gen = SignalGenerator(config)
signals = signal_gen.generate_signals(market_data)

print(f"Signal: {signals['signal']}")  # -1, 0, or 1
print(f"Confidence: {signals['confidence']}")  # 0 to 1
```

### Risk Management (`risk_management.py`)

Comprehensive risk control:

```python
from risk_management import RiskManager

risk_manager = RiskManager(config)

# Position sizing
position_size = risk_manager.calculate_position_size(
    'AAPL', confidence=0.8, price=150.0, volatility=0.25, returns=historical_returns
)

# Risk checks
can_trade, warnings = risk_manager.check_risk_before_trade(
    'AAPL', 'BUY', 100, 150.0
)
```

### Execution Engine (`execution_engine.py`)

Professional order execution:

```python
from execution_engine import ExecutionEngine

execution_engine = ExecutionEngine(config)
execution_engine.start()

# Submit order
order_id = execution_engine.submit_order(
    symbol='AAPL',
    side='BUY',
    quantity=100,
    order_type='MARKET'
)

# Use execution algorithm
order_id = execution_engine.submit_order(
    symbol='AAPL',
    side='BUY',
    quantity=1000,
    algorithm='TWAP'  # Break into time slices
)
```

### Backtesting (`backtesting.py`)

Comprehensive strategy validation:

```python
from backtesting import Backtester

backtester = Backtester(initial_capital=100000, commission=0.001)

result = backtester.run_backtest(
    data=market_data,
    signal_generator=signal_generator,
    risk_manager=risk_manager
)

print(f"Total Return: {result.performance_metrics['total_return']:.2%}")
print(f"Sharpe Ratio: {result.performance_metrics['sharpe_ratio']:.3f}")
print(f"Max Drawdown: {result.performance_metrics['max_drawdown']:.2%}")
```

## 📈 Performance Metrics

The system calculates comprehensive performance metrics:

### Return Metrics
- Total Return
- Annualized Return
- Volatility (annualized)
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio

### Risk Metrics
- Value at Risk (VaR)
- Conditional Value at Risk (CVaR)
- Maximum Drawdown
- Omega Ratio
- Skewness and Kurtosis

### Trade Analysis
- Hit Ratio (% profitable trades)
- Profit Factor
- Average Trade Duration
- Average Win/Loss

## 🔬 Advanced Features

### Monte Carlo Simulation

Bootstrap trade sequences to assess strategy robustness:

```python
from backtesting import MonteCarloSimulation

mc_sim = MonteCarloSimulation(n_simulations=1000)
results = mc_sim.run_simulation(trades_df)

print(f"Probability of Loss: {results['probability_of_loss']:.1%}")
print(f"VaR (5%): {results['value_at_risk_5']:.2%}")
```

### Walk-Forward Analysis

Out-of-sample testing with rolling windows:

```python
from backtesting import WalkForwardAnalysis

wf_analysis = WalkForwardAnalysis(train_period=252, test_period=63)
results = wf_analysis.run_analysis(data, strategy_function)

print(f"Consistency: {results['consistency']:.1%}")
print(f"Average Sharpe: {results['avg_sharpe']:.3f}")
```

### Machine Learning Integration

The system includes ML models for signal generation:

- **Random Forest**: Ensemble method for robust predictions
- **Gradient Boosting**: Sequential learning for complex patterns
- **Logistic Regression**: Linear model for interpretability
- **Support Vector Machine**: Non-linear classification

## ⚠️ Risk Warnings

- **Paper Trading**: Always test strategies in paper trading mode first
- **Risk Management**: Never risk more than you can afford to lose
- **Backtesting**: Past performance does not guarantee future results
- **Market Risk**: All trading involves substantial risk of loss
- **Technology Risk**: System failures can result in losses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **TA-Lib**: Technical Analysis Library
- **NumPy/Pandas**: Numerical computing
- **scikit-learn**: Machine learning algorithms
- **ARCH**: GARCH modeling
- **PyKalman**: Kalman filtering

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Review the documentation
- Check the examples in each module

---

**Disclaimer**: This software is for educational and research purposes. Trading financial instruments involves substantial risk of loss and is not suitable for all investors. The authors are not responsible for any financial losses incurred from using this software.
