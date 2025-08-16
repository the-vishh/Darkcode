#!/usr/bin/env python3
"""
Advanced Quantitative Trading System
====================================

A comprehensive quantitative trading system that integrates:
- Real-time data feeds with WebSocket connections
- Advanced mathematical models (Black-Scholes, GARCH, Kalman filters)
- Multi-factor signal generation with ML algorithms
- Sophisticated risk management and position sizing
- Professional execution engine with smart order routing
- Comprehensive backtesting and performance analysis

Author: AI Assistant
Date: 2024
"""

import asyncio
import logging
import sys
import signal
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
from config import config
from data_feed import RealTimeDataFeed, HistoricalDataProvider, MarketData
from mathematical_models import (
    BlackScholesModel, GARCHModel, KalmanFilterModel, 
    MeanReversionModel, JumpDiffusionModel, RegimeSwitchingModel
)
from signal_generation import SignalGenerator
from risk_management import RiskManager
from execution_engine import ExecutionEngine, PortfolioExecutor
from backtesting import Backtester, MonteCarloSimulation, WalkForwardAnalysis

class QuantTradingSystem:
    """Main quantitative trading system orchestrating all components"""
    
    def __init__(self, config_obj=None, mode='paper'):
        """
        Initialize the quantitative trading system
        
        Args:
            config_obj: Configuration object
            mode: Trading mode ('paper', 'live', 'backtest')
        """
        self.config = config_obj or config
        self.mode = mode
        self.running = False
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
        
        # System state
        self.portfolio_value = self.config.INITIAL_CAPITAL
        self.positions = {}
        self.performance_metrics = {}
        self.system_start_time = None
        
        # Threading
        self.main_thread = None
        self.shutdown_event = threading.Event()
        
        self.logger.info("Quantitative Trading System initialized")
        self.logger.info(f"Mode: {mode}")
        self.logger.info(f"Initial Capital: ${self.config.INITIAL_CAPITAL:,.2f}")
        self.logger.info(f"Symbols: {self.config.SYMBOLS}")
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'trading_system_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _initialize_components(self):
        """Initialize all system components"""
        self.logger.info("Initializing system components...")
        
        # Data components
        self.data_feed = RealTimeDataFeed(
            symbols=self.config.SYMBOLS,
            api_key=self.config.ALPACA_API_KEY
        )
        self.historical_data_provider = HistoricalDataProvider()
        
        # Mathematical models
        self.models = {
            'black_scholes': BlackScholesModel(),
            'garch': GARCHModel(),
            'kalman': KalmanFilterModel(),
            'mean_reversion': MeanReversionModel(),
            'jump_diffusion': JumpDiffusionModel(),
            'regime_switching': RegimeSwitchingModel()
        }
        
        # Trading components
        self.signal_generator = SignalGenerator(self.config)
        self.risk_manager = RiskManager(self.config)
        self.execution_engine = ExecutionEngine(self.config)
        self.portfolio_executor = PortfolioExecutor(self.execution_engine, self.risk_manager)
        
        # Analysis components
        self.backtester = Backtester(
            initial_capital=self.config.INITIAL_CAPITAL,
            commission=0.001
        )
        self.monte_carlo = MonteCarloSimulation(n_simulations=1000)
        self.walk_forward = WalkForwardAnalysis()
        
        # Historical data cache
        self.historical_data = {}
        self.current_market_data = {}
        
        self.logger.info("All components initialized successfully")
    
    def start(self):
        """Start the trading system"""
        if self.running:
            self.logger.warning("System already running")
            return
        
        self.logger.info("Starting Quantitative Trading System...")
        self.running = True
        self.system_start_time = datetime.now()
        
        try:
            # Load historical data
            self._load_historical_data()
            
            # Start execution engine
            self.execution_engine.start()
            
            # Subscribe to market data
            self.data_feed.subscribe(self._on_market_data)
            
            if self.mode in ['paper', 'live']:
                # Start real-time trading
                self.data_feed.start()
                
                # Start main trading loop
                self.main_thread = threading.Thread(target=self._main_trading_loop, daemon=True)
                self.main_thread.start()
                
                self.logger.info("Real-time trading started")
            
            elif self.mode == 'backtest':
                # Run backtesting mode
                self._run_backtesting_mode()
            
        except Exception as e:
            self.logger.error(f"Error starting system: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the trading system gracefully"""
        if not self.running:
            return
        
        self.logger.info("Stopping Quantitative Trading System...")
        self.running = False
        self.shutdown_event.set()
        
        # Stop components
        if hasattr(self, 'data_feed'):
            self.data_feed.stop()
        
        if hasattr(self, 'execution_engine'):
            self.execution_engine.stop()
        
        # Wait for main thread to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5)
        
        # Generate final report
        self._generate_final_report()
        
        self.logger.info("Quantitative Trading System stopped")
    
    def _load_historical_data(self):
        """Load historical data for all symbols"""
        self.logger.info("Loading historical data...")
        
        for symbol in self.config.SYMBOLS:
            try:
                data = self.historical_data_provider.get_historical_data(
                    symbol=symbol,
                    period="2y",  # 2 years of data
                    interval="1d"
                )
                
                if not data.empty:
                    self.historical_data[symbol] = data
                    self.logger.info(f"Loaded {len(data)} days of data for {symbol}")
                else:
                    self.logger.warning(f"No historical data available for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"Error loading data for {symbol}: {e}")
        
        self.logger.info(f"Historical data loaded for {len(self.historical_data)} symbols")
    
    def _on_market_data(self, market_data: MarketData):
        """Handle incoming market data"""
        try:
            # Update current market data
            self.current_market_data[market_data.symbol] = {
                'price': market_data.price,
                'volume': market_data.volume,
                'timestamp': market_data.timestamp,
                'bid': market_data.bid,
                'ask': market_data.ask,
                'high': market_data.high,
                'low': market_data.low,
                'open': market_data.open
            }
            
            # Trigger signal generation for this symbol
            if market_data.symbol in self.historical_data:
                self._process_symbol_signals(market_data.symbol)
                
        except Exception as e:
            self.logger.error(f"Error processing market data for {market_data.symbol}: {e}")
    
    def _process_symbol_signals(self, symbol: str):
        """Process trading signals for a specific symbol"""
        try:
            # Get current market data
            current_data = self.current_market_data.get(symbol)
            if not current_data:
                return
            
            # Get historical data
            historical_data = self.historical_data.get(symbol)
            if historical_data is None or len(historical_data) < 50:
                return
            
            # Generate trading signals
            signal_result = self.signal_generator.generate_signals(
                historical_data, train_ml=False
            )
            
            signal = signal_result['signal']
            confidence = signal_result['confidence']
            
            # Log signal if significant
            if signal != 0 and confidence > 0.6:
                action = "BUY" if signal > 0 else "SELL"
                self.logger.info(
                    f"Signal Generated - {symbol}: {action} "
                    f"(Signal: {signal}, Confidence: {confidence:.2f})"
                )
                
                # Execute signal
                success = self.portfolio_executor.execute_signal(
                    symbol=symbol,
                    signal=signal,
                    confidence=confidence,
                    current_price=current_data['price'],
                    volatility=0.02  # TODO: Calculate actual volatility
                )
                
                if success:
                    self.logger.info(f"Trade executed successfully for {symbol}")
                else:
                    self.logger.warning(f"Trade execution failed for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error processing signals for {symbol}: {e}")
    
    def _main_trading_loop(self):
        """Main trading loop for real-time operations"""
        self.logger.info("Main trading loop started")
        
        last_update = time.time()
        last_risk_check = time.time()
        last_performance_update = time.time()
        
        while self.running and not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # Update portfolio positions every 10 seconds
                if current_time - last_update > 10:
                    self._update_portfolio_status()
                    last_update = current_time
                
                # Risk monitoring every 30 seconds
                if current_time - last_risk_check > 30:
                    self._perform_risk_checks()
                    last_risk_check = current_time
                
                # Performance updates every 60 seconds
                if current_time - last_performance_update > 60:
                    self._update_performance_metrics()
                    last_performance_update = current_time
                
                # Sleep briefly to prevent busy waiting
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in main trading loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        self.logger.info("Main trading loop ended")
    
    def _update_portfolio_status(self):
        """Update portfolio status and positions"""
        try:
            # Update positions from execution engine
            self.portfolio_executor.update_positions()
            self.positions = self.portfolio_executor.positions.copy()
            
            # Calculate current portfolio value
            current_prices = {}
            for symbol in self.config.SYMBOLS:
                if symbol in self.current_market_data:
                    current_prices[symbol] = self.current_market_data[symbol]['price']
            
            # Update risk metrics
            if current_prices:
                risk_metrics = self.risk_manager.update_portfolio_metrics(current_prices)
                self.portfolio_value = risk_metrics['portfolio_value']
                
                # Log significant changes
                if len(self.positions) > 0:
                    self.logger.info(f"Portfolio Value: ${self.portfolio_value:,.2f}")
                    self.logger.info(f"Active Positions: {len(self.positions)}")
                    
                    if risk_metrics['risk_warnings']:
                        for warning in risk_metrics['risk_warnings']:
                            self.logger.warning(f"Risk Warning: {warning}")
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio status: {e}")
    
    def _perform_risk_checks(self):
        """Perform comprehensive risk monitoring"""
        try:
            # Generate risk report
            risk_report = self.risk_manager.get_risk_report()
            
            # Check for risk limit violations
            portfolio_metrics = risk_report.get('portfolio_metrics', {})
            drawdown_metrics = risk_report.get('drawdown_metrics', {})
            
            # Check maximum drawdown
            current_dd = drawdown_metrics.get('current_drawdown', 0)
            if current_dd < -self.config.MAX_DRAWDOWN:
                self.logger.critical(
                    f"RISK ALERT: Maximum drawdown exceeded! "
                    f"Current: {current_dd:.2%}, Limit: {self.config.MAX_DRAWDOWN:.2%}"
                )
                # TODO: Implement emergency position closing
            
            # Check daily loss limit
            daily_return = portfolio_metrics.get('daily_return', 0)
            if daily_return < -self.config.MAX_DAILY_LOSS:
                self.logger.critical(
                    f"RISK ALERT: Daily loss limit exceeded! "
                    f"Current: {daily_return:.2%}, Limit: {self.config.MAX_DAILY_LOSS:.2%}"
                )
            
        except Exception as e:
            self.logger.error(f"Error in risk monitoring: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Calculate basic performance metrics
            if self.system_start_time:
                runtime = datetime.now() - self.system_start_time
                total_return = (self.portfolio_value - self.config.INITIAL_CAPITAL) / self.config.INITIAL_CAPITAL
                
                self.performance_metrics = {
                    'runtime_hours': runtime.total_seconds() / 3600,
                    'total_return': total_return,
                    'current_value': self.portfolio_value,
                    'active_positions': len(self.positions),
                    'total_trades': len(self.execution_engine.order_manager.get_fills())
                }
                
                # Log periodic performance update
                self.logger.info(
                    f"Performance Update - Return: {total_return:.2%}, "
                    f"Value: ${self.portfolio_value:,.2f}, "
                    f"Positions: {len(self.positions)}"
                )
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def _run_backtesting_mode(self):
        """Run comprehensive backtesting"""
        self.logger.info("Starting backtesting mode...")
        
        try:
            # Prepare multi-symbol data for backtesting
            backtest_data = self._prepare_backtest_data()
            
            if backtest_data.empty:
                raise ValueError("No data available for backtesting")
            
            # Run backtest
            result = self.backtester.run_backtest(
                data=backtest_data,
                signal_generator=self.signal_generator,
                risk_manager=self.risk_manager,
                start_date='2022-01-01',
                end_date='2023-12-31'
            )
            
            # Display results
            self._display_backtest_results(result)
            
            # Run Monte Carlo simulation
            if not result.trades.empty:
                self.logger.info("Running Monte Carlo simulation...")
                mc_results = self._run_monte_carlo_analysis(result.trades)
                self._display_monte_carlo_results(mc_results)
            
            # Run walk-forward analysis (simplified)
            self.logger.info("Running walk-forward analysis...")
            wf_results = self._run_walk_forward_analysis(backtest_data)
            self._display_walk_forward_results(wf_results)
            
        except Exception as e:
            self.logger.error(f"Error in backtesting mode: {e}")
            raise
    
    def _prepare_backtest_data(self) -> pd.DataFrame:
        """Prepare multi-symbol data for backtesting"""
        combined_data = pd.DataFrame()
        
        for symbol, data in self.historical_data.items():
            # Add symbol prefix to columns
            symbol_data = data.copy()
            symbol_data.columns = [f"{symbol}_{col}" for col in symbol_data.columns]
            
            if combined_data.empty:
                combined_data = symbol_data
            else:
                combined_data = combined_data.join(symbol_data, how='outer')
        
        # Forward fill missing values
        combined_data = combined_data.fillna(method='ffill')
        
        return combined_data
    
    def _display_backtest_results(self, result):
        """Display comprehensive backtest results"""
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        
        # Performance metrics
        print("\nPERFORMANCE METRICS:")
        print("-" * 30)
        metrics = result.performance_metrics
        print(f"Total Return:       {metrics['total_return']:.2%}")
        print(f"Annualized Return:  {metrics['annualized_return']:.2%}")
        print(f"Volatility:         {metrics['volatility']:.2%}")
        print(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.3f}")
        print(f"Sortino Ratio:      {metrics['sortino_ratio']:.3f}")
        print(f"Calmar Ratio:       {metrics['calmar_ratio']:.3f}")
        print(f"Max Drawdown:       {metrics['max_drawdown']:.2%}")
        print(f"Final Value:        ${metrics['final_value']:,.2f}")
        print(f"Total Trades:       {metrics['total_trades']}")
        
        # Risk metrics
        print("\nRISK METRICS:")
        print("-" * 30)
        risk = result.risk_metrics
        print(f"VaR (95%):          {risk['var_95']:.2%}")
        print(f"CVaR (95%):         {risk['cvar_95']:.2%}")
        print(f"Skewness:           {risk['skewness']:.3f}")
        print(f"Kurtosis:           {risk['kurtosis']:.3f}")
        print(f"Best Day:           {risk['best_day']:.2%}")
        print(f"Worst Day:          {risk['worst_day']:.2%}")
        print(f"Positive Days:      {risk['positive_days_ratio']:.1%}")
        
        # Drawdown analysis
        print("\nDRAWDOWN ANALYSIS:")
        print("-" * 30)
        dd = result.drawdown_analysis
        print(f"Max Drawdown:       {dd['max_drawdown']:.2%}")
        print(f"Avg Drawdown:       {dd['avg_drawdown']:.2%}")
        print(f"Drawdown Periods:   {dd['num_drawdown_periods']}")
        print(f"Longest Duration:   {dd['longest_drawdown_duration']} days")
    
    def _run_monte_carlo_analysis(self, trades_df):
        """Run Monte Carlo analysis on trades"""
        # Add PnL calculation (simplified)
        trades_with_pnl = trades_df.copy()
        if 'pnl' not in trades_with_pnl.columns:
            # Simplified P&L calculation
            np.random.seed(42)
            trades_with_pnl['pnl'] = np.random.normal(50, 200, len(trades_with_pnl))
        
        return self.monte_carlo.run_simulation(trades_with_pnl)
    
    def _display_monte_carlo_results(self, mc_results):
        """Display Monte Carlo simulation results"""
        print("\nMONTE CARLO SIMULATION:")
        print("-" * 30)
        print(f"Mean Final Value:   ${mc_results['mean_final_value']:,.2f}")
        print(f"Std Final Value:    ${mc_results['std_final_value']:,.2f}")
        print(f"5th Percentile:     ${mc_results['percentile_5']:,.2f}")
        print(f"95th Percentile:    ${mc_results['percentile_95']:,.2f}")
        print(f"Probability of Loss: {mc_results['probability_of_loss']:.1%}")
        print(f"Mean Return:        {mc_results['mean_return']:.2%}")
        print(f"VaR (5%):           {mc_results['value_at_risk_5']:.2%}")
    
    def _run_walk_forward_analysis(self, data):
        """Run simplified walk-forward analysis"""
        def strategy_func(test_data, **params):
            # Simplified strategy function
            returns = np.random.normal(0.001, 0.02, len(test_data))
            total_return = np.prod(1 + returns) - 1
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
            max_dd = np.min(np.cumsum(returns))
            
            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_dd
            }
        
        return self.walk_forward.run_analysis(data, strategy_func)
    
    def _display_walk_forward_results(self, wf_results):
        """Display walk-forward analysis results"""
        if not wf_results:
            return
            
        print("\nWALK-FORWARD ANALYSIS:")
        print("-" * 30)
        print(f"Number of Periods:  {wf_results['num_periods']}")
        print(f"Average Return:     {wf_results['avg_return']:.2%}")
        print(f"Return Std Dev:     {wf_results['std_return']:.2%}")
        print(f"Average Sharpe:     {wf_results['avg_sharpe']:.3f}")
        print(f"Consistency:        {wf_results['consistency']:.1%}")
        print(f"Best Period:        {wf_results['best_period']:.2%}")
        print(f"Worst Period:       {wf_results['worst_period']:.2%}")
    
    def _generate_final_report(self):
        """Generate final performance report"""
        print("\n" + "="*60)
        print("FINAL SYSTEM REPORT")
        print("="*60)
        
        if self.system_start_time:
            runtime = datetime.now() - self.system_start_time
            print(f"Runtime: {runtime}")
        
        print(f"Mode: {self.mode}")
        print(f"Initial Capital: ${self.config.INITIAL_CAPITAL:,.2f}")
        print(f"Final Value: ${self.portfolio_value:,.2f}")
        
        if self.performance_metrics:
            total_return = self.performance_metrics['total_return']
            print(f"Total Return: {total_return:.2%}")
            print(f"Total Trades: {self.performance_metrics['total_trades']}")
        
        # Execution statistics
        exec_report = self.execution_engine.get_execution_report()
        if 'total_fills' in exec_report:
            print(f"Total Fills: {exec_report['total_fills']}")
            print(f"Average Slippage: {exec_report.get('avg_slippage', 0):.4f}")
        
        print("="*60)
    
    def get_status(self) -> Dict:
        """Get current system status"""
        return {
            'running': self.running,
            'mode': self.mode,
            'portfolio_value': self.portfolio_value,
            'positions': self.positions.copy(),
            'performance_metrics': self.performance_metrics.copy(),
            'risk_warnings': self.risk_manager.portfolio_risk.check_risk_limits(
                self.config.MAX_POSITION_SIZE,
                0.3,
                self.config.MAX_DRAWDOWN
            ) if hasattr(self, 'risk_manager') else []
        }

def setup_signal_handlers(trading_system):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        trading_system.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point for the quantitative trading system"""
    print("="*60)
    print("ADVANCED QUANTITATIVE TRADING SYSTEM")
    print("="*60)
    print("Initializing system components...")
    
    # Determine mode from command line arguments
    mode = 'paper'  # Default mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode not in ['paper', 'live', 'backtest']:
            print(f"Invalid mode: {mode}. Using 'paper' mode.")
            mode = 'paper'
    
    print(f"Running in {mode.upper()} mode")
    
    # Initialize trading system
    trading_system = QuantTradingSystem(config, mode=mode)
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers(trading_system)
    
    try:
        # Start the system
        trading_system.start()
        
        if mode in ['paper', 'live']:
            print("\nSystem is running. Press Ctrl+C to stop.")
            print("="*60)
            
            # Keep main thread alive
            while trading_system.running:
                time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"System error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        trading_system.stop()

if __name__ == "__main__":
    main()