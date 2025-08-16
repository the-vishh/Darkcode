import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class BacktestResult:
    """Container for backtest results"""
    equity_curve: pd.Series
    trades: pd.DataFrame
    daily_returns: pd.Series
    positions: pd.DataFrame
    performance_metrics: Dict
    drawdown_analysis: Dict
    risk_metrics: Dict

class PerformanceMetrics:
    """Calculate comprehensive performance metrics"""
    
    @staticmethod
    def total_return(equity_curve: pd.Series) -> float:
        """Total return over the period"""
        if len(equity_curve) < 2:
            return 0.0
        return (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]
    
    @staticmethod
    def annualized_return(equity_curve: pd.Series, trading_days: int = 252) -> float:
        """Annualized return"""
        total_ret = PerformanceMetrics.total_return(equity_curve)
        years = len(equity_curve) / trading_days
        if years <= 0:
            return 0.0
        return (1 + total_ret) ** (1 / years) - 1
    
    @staticmethod
    def volatility(daily_returns: pd.Series, trading_days: int = 252) -> float:
        """Annualized volatility"""
        return daily_returns.std() * np.sqrt(trading_days)
    
    @staticmethod
    def sharpe_ratio(daily_returns: pd.Series, risk_free_rate: float = 0.02,
                    trading_days: int = 252) -> float:
        """Sharpe ratio"""
        excess_returns = daily_returns.mean() * trading_days - risk_free_rate
        vol = PerformanceMetrics.volatility(daily_returns, trading_days)
        return excess_returns / vol if vol != 0 else 0.0
    
    @staticmethod
    def sortino_ratio(daily_returns: pd.Series, risk_free_rate: float = 0.02,
                     trading_days: int = 252) -> float:
        """Sortino ratio (downside deviation)"""
        excess_returns = daily_returns.mean() * trading_days - risk_free_rate
        downside_returns = daily_returns[daily_returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(trading_days)
        return excess_returns / downside_vol if downside_vol != 0 else 0.0
    
    @staticmethod
    def calmar_ratio(equity_curve: pd.Series, trading_days: int = 252) -> float:
        """Calmar ratio (annualized return / max drawdown)"""
        ann_return = PerformanceMetrics.annualized_return(equity_curve, trading_days)
        max_dd = PerformanceMetrics.max_drawdown(equity_curve)
        return ann_return / abs(max_dd) if max_dd != 0 else 0.0
    
    @staticmethod
    def max_drawdown(equity_curve: pd.Series) -> float:
        """Maximum drawdown"""
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min()
    
    @staticmethod
    def var_95(daily_returns: pd.Series) -> float:
        """Value at Risk (95% confidence)"""
        return np.percentile(daily_returns, 5)
    
    @staticmethod
    def cvar_95(daily_returns: pd.Series) -> float:
        """Conditional Value at Risk (95% confidence)"""
        var_95 = PerformanceMetrics.var_95(daily_returns)
        return daily_returns[daily_returns <= var_95].mean()
    
    @staticmethod
    def omega_ratio(daily_returns: pd.Series, threshold: float = 0.0) -> float:
        """Omega ratio"""
        excess_returns = daily_returns - threshold
        gains = excess_returns[excess_returns > 0].sum()
        losses = abs(excess_returns[excess_returns < 0].sum())
        return gains / losses if losses != 0 else np.inf
    
    @staticmethod
    def hit_ratio(trades: pd.DataFrame) -> float:
        """Percentage of profitable trades"""
        if len(trades) == 0:
            return 0.0
        profitable_trades = len(trades[trades['pnl'] > 0])
        return profitable_trades / len(trades)
    
    @staticmethod
    def profit_factor(trades: pd.DataFrame) -> float:
        """Ratio of gross profit to gross loss"""
        if len(trades) == 0:
            return 0.0
        gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())
        return gross_profit / gross_loss if gross_loss != 0 else np.inf
    
    @staticmethod
    def avg_trade_duration(trades: pd.DataFrame) -> float:
        """Average trade duration in days"""
        if len(trades) == 0:
            return 0.0
        durations = (trades['exit_time'] - trades['entry_time']).dt.days
        return durations.mean()

class DrawdownAnalysis:
    """Detailed drawdown analysis"""
    
    @staticmethod
    def calculate_drawdowns(equity_curve: pd.Series) -> pd.DataFrame:
        """Calculate all drawdown periods"""
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        
        # Find drawdown periods
        in_drawdown = drawdown < 0
        drawdown_periods = []
        
        start_idx = None
        for i, is_dd in enumerate(in_drawdown):
            if is_dd and start_idx is None:
                start_idx = i
            elif not is_dd and start_idx is not None:
                end_idx = i - 1
                dd_period = {
                    'start_date': equity_curve.index[start_idx],
                    'end_date': equity_curve.index[end_idx],
                    'duration': end_idx - start_idx + 1,
                    'max_drawdown': drawdown.iloc[start_idx:end_idx+1].min(),
                    'recovery_date': equity_curve.index[i] if i < len(equity_curve) else None
                }
                drawdown_periods.append(dd_period)
                start_idx = None
        
        # Handle ongoing drawdown
        if start_idx is not None:
            dd_period = {
                'start_date': equity_curve.index[start_idx],
                'end_date': equity_curve.index[-1],
                'duration': len(equity_curve) - start_idx,
                'max_drawdown': drawdown.iloc[start_idx:].min(),
                'recovery_date': None
            }
            drawdown_periods.append(dd_period)
        
        return pd.DataFrame(drawdown_periods)
    
    @staticmethod
    def underwater_curve(equity_curve: pd.Series) -> pd.Series:
        """Generate underwater curve"""
        peak = equity_curve.expanding().max()
        return (equity_curve - peak) / peak

class MonteCarloSimulation:
    """Monte Carlo simulation for strategy robustness testing"""
    
    def __init__(self, n_simulations: int = 1000):
        self.n_simulations = n_simulations
    
    def bootstrap_trades(self, trades: pd.DataFrame) -> BacktestResult:
        """Bootstrap trade sequence"""
        n_trades = len(trades)
        if n_trades == 0:
            return None
        
        # Sample trades with replacement
        sampled_indices = np.random.choice(n_trades, size=n_trades, replace=True)
        sampled_trades = trades.iloc[sampled_indices].copy()
        
        # Reconstruct equity curve
        initial_capital = 100000  # Assuming standard initial capital
        equity = [initial_capital]
        
        for _, trade in sampled_trades.iterrows():
            equity.append(equity[-1] + trade['pnl'])
        
        equity_series = pd.Series(equity[1:], index=sampled_trades.index)
        daily_returns = equity_series.pct_change().dropna()
        
        return {
            'equity_curve': equity_series,
            'trades': sampled_trades,
            'daily_returns': daily_returns,
            'final_value': equity[-1],
            'total_return': (equity[-1] - equity[0]) / equity[0]
        }
    
    def run_simulation(self, trades: pd.DataFrame) -> Dict:
        """Run Monte Carlo simulation"""
        results = []
        
        for i in range(self.n_simulations):
            sim_result = self.bootstrap_trades(trades)
            if sim_result:
                results.append(sim_result)
        
        if not results:
            return {}
        
        # Analyze results
        final_values = [r['final_value'] for r in results]
        total_returns = [r['total_return'] for r in results]
        
        return {
            'mean_final_value': np.mean(final_values),
            'std_final_value': np.std(final_values),
            'percentile_5': np.percentile(final_values, 5),
            'percentile_95': np.percentile(final_values, 95),
            'probability_of_loss': len([r for r in total_returns if r < 0]) / len(total_returns),
            'mean_return': np.mean(total_returns),
            'std_return': np.std(total_returns),
            'value_at_risk_5': np.percentile(total_returns, 5)
        }

class WalkForwardAnalysis:
    """Walk-forward analysis for out-of-sample testing"""
    
    def __init__(self, train_period: int = 252, test_period: int = 63, step_size: int = 21):
        self.train_period = train_period  # Training period in days
        self.test_period = test_period    # Testing period in days
        self.step_size = step_size        # Step size for rolling window
    
    def run_analysis(self, data: pd.DataFrame, strategy_func, 
                    optimization_func=None) -> Dict:
        """Run walk-forward analysis"""
        results = []
        start_idx = 0
        
        while start_idx + self.train_period + self.test_period <= len(data):
            # Define training and testing periods
            train_end = start_idx + self.train_period
            test_end = train_end + self.test_period
            
            train_data = data.iloc[start_idx:train_end]
            test_data = data.iloc[train_end:test_end]
            
            # Optimize strategy on training data (if optimization function provided)
            if optimization_func:
                optimal_params = optimization_func(train_data)
            else:
                optimal_params = {}
            
            # Test strategy on out-of-sample data
            test_result = strategy_func(test_data, **optimal_params)
            
            period_result = {
                'train_start': train_data.index[0],
                'train_end': train_data.index[-1],
                'test_start': test_data.index[0],
                'test_end': test_data.index[-1],
                'optimal_params': optimal_params,
                'test_performance': test_result
            }
            
            results.append(period_result)
            start_idx += self.step_size
        
        return self._analyze_walk_forward_results(results)
    
    def _analyze_walk_forward_results(self, results: List[Dict]) -> Dict:
        """Analyze walk-forward results"""
        if not results:
            return {}
        
        # Extract performance metrics from each period
        returns = []
        sharpe_ratios = []
        max_drawdowns = []
        
        for result in results:
            perf = result['test_performance']
            if 'total_return' in perf:
                returns.append(perf['total_return'])
            if 'sharpe_ratio' in perf:
                sharpe_ratios.append(perf['sharpe_ratio'])
            if 'max_drawdown' in perf:
                max_drawdowns.append(perf['max_drawdown'])
        
        return {
            'num_periods': len(results),
            'avg_return': np.mean(returns) if returns else 0,
            'std_return': np.std(returns) if returns else 0,
            'avg_sharpe': np.mean(sharpe_ratios) if sharpe_ratios else 0,
            'consistency': len([r for r in returns if r > 0]) / len(returns) if returns else 0,
            'worst_period': min(returns) if returns else 0,
            'best_period': max(returns) if returns else 0,
            'detailed_results': results
        }

class Backtester:
    """Main backtesting engine"""
    
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()
    
    def reset(self):
        """Reset backtester state"""
        self.equity = [self.initial_capital]
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_data = []
        
    def run_backtest(self, data: pd.DataFrame, signal_generator,
                    risk_manager=None, start_date=None, end_date=None) -> BacktestResult:
        """Run comprehensive backtest"""
        self.reset()
        
        # Filter data by date range if specified
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if len(data) < 2:
            raise ValueError("Insufficient data for backtesting")
        
        print(f"Running backtest from {data.index[0]} to {data.index[-1]}")
        print(f"Initial capital: ${self.initial_capital:,.2f}")
        
        # Process each day
        for i, (date, row) in enumerate(data.iterrows()):
            if i == 0:
                continue  # Skip first day (need previous data for signals)
            
            # Get data up to current date for signal generation
            historical_data = data.iloc[:i+1]
            
            # Generate signals for all symbols
            symbols = [col.replace('_Close', '') for col in data.columns if col.endswith('_Close')]
            
            for symbol in symbols:
                symbol_data = self._extract_symbol_data(historical_data, symbol)
                if len(symbol_data) < 20:  # Need minimum data for indicators
                    continue
                
                try:
                    # Generate trading signal
                    signal_result = signal_generator.generate_signals(symbol_data, train_ml=False)
                    signal = signal_result['signal']
                    confidence = signal_result['confidence']
                    
                    current_price = row[f'{symbol}_Close']
                    
                    # Execute trade based on signal
                    if signal != 0:
                        self._execute_trade(symbol, signal, confidence, current_price, 
                                          date, risk_manager)
                
                except Exception as e:
                    print(f"Error processing {symbol} on {date}: {e}")
                    continue
            
            # Update portfolio value
            portfolio_value = self._calculate_portfolio_value(data.iloc[i])
            self.equity.append(portfolio_value)
            
            # Store daily data
            daily_data_point = {
                'date': date,
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'positions': self.positions.copy()
            }
            self.daily_data.append(daily_data_point)
        
        return self._compile_results(data)
    
    def _extract_symbol_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Extract OHLCV data for a specific symbol"""
        required_cols = [f'{symbol}_Open', f'{symbol}_High', f'{symbol}_Low', 
                        f'{symbol}_Close', f'{symbol}_Volume']
        
        available_cols = [col for col in required_cols if col in data.columns]
        if len(available_cols) < 4:  # At least OHLC
            return pd.DataFrame()
        
        symbol_data = data[available_cols].copy()
        symbol_data.columns = [col.replace(f'{symbol}_', '') for col in symbol_data.columns]
        
        return symbol_data.dropna()
    
    def _execute_trade(self, symbol: str, signal: int, confidence: float,
                      price: float, date, risk_manager=None):
        """Execute a trade based on signal"""
        
        current_position = self.positions.get(symbol, 0)
        
        # Determine trade action
        if signal > 0 and current_position <= 0:
            # Buy signal
            action = 'BUY'
            target_position = self._calculate_position_size(symbol, confidence, price, risk_manager)
            quantity = target_position - current_position
        elif signal < 0 and current_position >= 0:
            # Sell signal  
            action = 'SELL'
            target_position = -self._calculate_position_size(symbol, confidence, price, risk_manager)
            quantity = current_position - target_position
        else:
            return  # No action needed
        
        if quantity == 0:
            return
        
        # Check if we have enough cash for buying
        trade_value = abs(quantity) * price
        commission_cost = trade_value * self.commission
        
        if action == 'BUY' and self.cash < trade_value + commission_cost:
            # Adjust quantity based on available cash
            available_for_trade = self.cash * 0.95  # Keep 5% cash buffer
            quantity = int((available_for_trade - commission_cost) / price)
            if quantity <= 0:
                return
        
        # Execute trade
        self._place_trade(symbol, action, quantity, price, date)
    
    def _calculate_position_size(self, symbol: str, confidence: float, price: float,
                               risk_manager=None) -> int:
        """Calculate position size"""
        if risk_manager:
            # Use risk manager for position sizing
            historical_returns = np.random.normal(0.001, 0.02, 100)  # Placeholder
            volatility = 0.02  # Placeholder
            return risk_manager.calculate_position_size(
                symbol, confidence, price, volatility, historical_returns
            )
        else:
            # Simple position sizing based on confidence and available capital
            portfolio_value = self.cash + sum(
                pos * price for pos in self.positions.values()  # Simplified
            )
            max_position_value = portfolio_value * 0.1 * confidence  # Max 10% per position
            return int(max_position_value / price)
    
    def _place_trade(self, symbol: str, action: str, quantity: int, price: float, date):
        """Place and record a trade"""
        trade_value = quantity * price
        commission = trade_value * self.commission
        
        # Update cash and positions
        if action == 'BUY':
            self.cash -= trade_value + commission
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        else:  # SELL
            self.cash += trade_value - commission
            self.positions[symbol] = self.positions.get(symbol, 0) - quantity
        
        # Record trade
        trade_record = {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'value': trade_value,
            'commission': commission,
            'date': date,
            'cash_after': self.cash
        }
        self.trades.append(trade_record)
        
        # Clean up zero positions
        if symbol in self.positions and self.positions[symbol] == 0:
            del self.positions[symbol]
    
    def _calculate_portfolio_value(self, current_prices: pd.Series) -> float:
        """Calculate current portfolio value"""
        portfolio_value = self.cash
        
        for symbol, position in self.positions.items():
            price_col = f'{symbol}_Close'
            if price_col in current_prices:
                portfolio_value += position * current_prices[price_col]
            else:
                # If price not available, use last known price (simplified)
                portfolio_value += position * 100  # Placeholder
        
        return portfolio_value
    
    def _compile_results(self, data: pd.DataFrame) -> BacktestResult:
        """Compile backtest results"""
        
        # Create equity curve
        equity_curve = pd.Series(self.equity[1:], index=data.index[:len(self.equity)-1])
        
        # Calculate daily returns
        daily_returns = equity_curve.pct_change().dropna()
        
        # Create trades DataFrame
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        
        # Create positions DataFrame
        positions_data = []
        for daily_data in self.daily_data:
            for symbol, position in daily_data['positions'].items():
                positions_data.append({
                    'date': daily_data['date'],
                    'symbol': symbol,
                    'position': position
                })
        positions_df = pd.DataFrame(positions_data)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(equity_curve, daily_returns, trades_df)
        
        # Calculate drawdown analysis
        drawdown_analysis = self._calculate_drawdown_analysis(equity_curve)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(daily_returns)
        
        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades_df,
            daily_returns=daily_returns,
            positions=positions_df,
            performance_metrics=performance_metrics,
            drawdown_analysis=drawdown_analysis,
            risk_metrics=risk_metrics
        )
    
    def _calculate_performance_metrics(self, equity_curve: pd.Series, 
                                     daily_returns: pd.Series, trades_df: pd.DataFrame) -> Dict:
        """Calculate comprehensive performance metrics"""
        return {
            'total_return': PerformanceMetrics.total_return(equity_curve),
            'annualized_return': PerformanceMetrics.annualized_return(equity_curve),
            'volatility': PerformanceMetrics.volatility(daily_returns),
            'sharpe_ratio': PerformanceMetrics.sharpe_ratio(daily_returns),
            'sortino_ratio': PerformanceMetrics.sortino_ratio(daily_returns),
            'calmar_ratio': PerformanceMetrics.calmar_ratio(equity_curve),
            'max_drawdown': PerformanceMetrics.max_drawdown(equity_curve),
            'omega_ratio': PerformanceMetrics.omega_ratio(daily_returns),
            'hit_ratio': PerformanceMetrics.hit_ratio(trades_df) if not trades_df.empty else 0,
            'profit_factor': PerformanceMetrics.profit_factor(trades_df) if not trades_df.empty else 0,
            'total_trades': len(trades_df),
            'final_value': equity_curve.iloc[-1] if len(equity_curve) > 0 else self.initial_capital
        }
    
    def _calculate_drawdown_analysis(self, equity_curve: pd.Series) -> Dict:
        """Calculate detailed drawdown analysis"""
        drawdown_periods = DrawdownAnalysis.calculate_drawdowns(equity_curve)
        underwater_curve = DrawdownAnalysis.underwater_curve(equity_curve)
        
        return {
            'max_drawdown': PerformanceMetrics.max_drawdown(equity_curve),
            'avg_drawdown': underwater_curve[underwater_curve < 0].mean() if len(underwater_curve[underwater_curve < 0]) > 0 else 0,
            'num_drawdown_periods': len(drawdown_periods),
            'longest_drawdown_duration': drawdown_periods['duration'].max() if len(drawdown_periods) > 0 else 0,
            'underwater_curve': underwater_curve,
            'drawdown_periods': drawdown_periods
        }
    
    def _calculate_risk_metrics(self, daily_returns: pd.Series) -> Dict:
        """Calculate risk metrics"""
        return {
            'var_95': PerformanceMetrics.var_95(daily_returns),
            'cvar_95': PerformanceMetrics.cvar_95(daily_returns),
            'skewness': daily_returns.skew(),
            'kurtosis': daily_returns.kurtosis(),
            'worst_day': daily_returns.min(),
            'best_day': daily_returns.max(),
            'positive_days_ratio': len(daily_returns[daily_returns > 0]) / len(daily_returns) if len(daily_returns) > 0 else 0
        }

def create_sample_data(symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
    """Create sample OHLCV data for backtesting"""
    np.random.seed(42)
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    data = pd.DataFrame(index=date_range)
    
    for symbol in symbols:
        # Generate realistic price data using geometric Brownian motion
        n_days = len(date_range)
        returns = np.random.normal(0.0005, 0.02, n_days)  # 0.05% daily return, 2% volatility
        prices = 100 * np.exp(np.cumsum(returns))
        
        # Create OHLCV data
        data[f'{symbol}_Open'] = prices * (1 + np.random.normal(0, 0.001, n_days))
        data[f'{symbol}_High'] = prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
        data[f'{symbol}_Low'] = prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
        data[f'{symbol}_Close'] = prices
        data[f'{symbol}_Volume'] = np.random.lognormal(15, 0.5, n_days)  # Realistic volume distribution
    
    return data

# Example usage and testing
if __name__ == "__main__":
    from signal_generation import SignalGenerator
    from risk_management import RiskManager
    from config import config
    
    print("Backtesting Framework Test")
    print("=" * 40)
    
    # Create sample data
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    data = create_sample_data(symbols, '2020-01-01', '2023-12-31')
    
    print(f"Generated data for {len(symbols)} symbols from {data.index[0]} to {data.index[-1]}")
    print(f"Total data points: {len(data)}")
    
    # Initialize components
    signal_generator = SignalGenerator(config)
    risk_manager = RiskManager(config)
    backtester = Backtester(initial_capital=100000, commission=0.001)
    
    # Run backtest
    print("\nRunning backtest...")
    try:
        result = backtester.run_backtest(
            data=data,
            signal_generator=signal_generator,
            risk_manager=risk_manager,
            start_date='2020-06-01',  # Start after some warm-up period
            end_date='2023-06-01'
        )
        
        print("\nBacktest Results:")
        print("=" * 30)
        
        # Performance metrics
        print("PERFORMANCE METRICS:")
        for metric, value in result.performance_metrics.items():
            if isinstance(value, float):
                if 'ratio' in metric or 'return' in metric:
                    print(f"{metric}: {value:.2%}")
                else:
                    print(f"{metric}: {value:.4f}")
            else:
                print(f"{metric}: {value}")
        
        print("\nRISK METRICS:")
        for metric, value in result.risk_metrics.items():
            if isinstance(value, float):
                if 'ratio' in metric:
                    print(f"{metric}: {value:.2%}")
                else:
                    print(f"{metric}: {value:.4f}")
            else:
                print(f"{metric}: {value}")
        
        print("\nDRAWDOWN ANALYSIS:")
        for metric, value in result.drawdown_analysis.items():
            if metric not in ['underwater_curve', 'drawdown_periods']:
                if isinstance(value, float):
                    if 'drawdown' in metric:
                        print(f"{metric}: {value:.2%}")
                    else:
                        print(f"{metric}: {value:.2f}")
                else:
                    print(f"{metric}: {value}")
        
        print(f"\nTotal trades executed: {len(result.trades)}")
        print(f"Final portfolio value: ${result.performance_metrics['final_value']:,.2f}")
        
        # Monte Carlo simulation
        print("\nRunning Monte Carlo simulation...")
        mc_sim = MonteCarloSimulation(n_simulations=1000)
        
        # For MC simulation, we need trade-level data
        if not result.trades.empty:
            # Calculate P&L per trade (simplified)
            trades_with_pnl = result.trades.copy()
            trades_with_pnl['pnl'] = np.random.normal(100, 500, len(trades_with_pnl))  # Placeholder
            
            mc_results = mc_sim.run_simulation(trades_with_pnl)
            
            print("MONTE CARLO RESULTS:")
            for metric, value in mc_results.items():
                if isinstance(value, float):
                    if 'probability' in metric or 'return' in metric:
                        print(f"{metric}: {value:.2%}")
                    else:
                        print(f"{metric}: {value:.2f}")
                else:
                    print(f"{metric}: {value}")
        
    except Exception as e:
        print(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nBacktesting framework test completed!")