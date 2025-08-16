#!/usr/bin/env python3
"""
Quantitative Trading System Demo
===============================

A demonstration of the comprehensive quantitative trading system
showing the architecture and capabilities without external dependencies.
"""

import time
import random
import math
from datetime import datetime

class SimpleDemo:
    """Demonstration of the quantitative trading system"""
    
    def __init__(self):
        self.initial_capital = 100000
        self.portfolio_value = self.initial_capital
        self.positions = {}
        self.trades = []
        self.signals_generated = 0
        self.trades_executed = 0
        
    def generate_mock_price(self, base_price=100):
        """Generate realistic stock price movement"""
        # Simple geometric Brownian motion simulation
        drift = 0.0001  # Small positive drift
        volatility = 0.02  # 2% daily volatility
        random_shock = random.normalvariate(0, 1) * volatility
        return base_price * (1 + drift + random_shock)
    
    def calculate_rsi(self, prices, period=14):
        """Simple RSI calculation"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26):
        """Simple MACD calculation"""
        if len(prices) < slow:
            return 0, 0
        
        # Simple moving averages (in real system, would use EMA)
        ema_fast = sum(prices[-fast:]) / fast
        ema_slow = sum(prices[-slow:]) / slow
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.9  # Simplified signal line
        
        return macd_line, signal_line
    
    def generate_signal(self, symbol, price_history):
        """Generate trading signal using technical indicators"""
        if len(price_history) < 30:
            return 0, 0.5  # No signal, neutral confidence
        
        # Calculate technical indicators
        rsi = self.calculate_rsi(price_history)
        macd_line, macd_signal = self.calculate_macd(price_history)
        
        # Simple moving average crossover
        sma_5 = sum(price_history[-5:]) / 5
        sma_20 = sum(price_history[-20:]) / 20
        
        # Generate signals
        signal_strength = 0
        confidence_factors = []
        
        # RSI signals
        if rsi < 30:  # Oversold
            signal_strength += 1
            confidence_factors.append(0.8)
        elif rsi > 70:  # Overbought
            signal_strength -= 1
            confidence_factors.append(0.8)
        
        # MACD signals
        if macd_line > macd_signal:
            signal_strength += 0.5
            confidence_factors.append(0.6)
        else:
            signal_strength -= 0.5
            confidence_factors.append(0.6)
        
        # Moving average signals
        if sma_5 > sma_20:
            signal_strength += 0.5
            confidence_factors.append(0.7)
        else:
            signal_strength -= 0.5
            confidence_factors.append(0.7)
        
        # Normalize signal to -1, 0, 1
        if signal_strength > 0.5:
            final_signal = 1  # Buy
        elif signal_strength < -0.5:
            final_signal = -1  # Sell
        else:
            final_signal = 0  # Hold
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        confidence = min(confidence, 1.0)
        
        self.signals_generated += 1
        return final_signal, confidence
    
    def calculate_position_size(self, symbol, confidence, price):
        """Calculate position size based on Kelly Criterion approximation"""
        # Simplified Kelly Criterion
        win_rate = 0.55  # Assume 55% win rate
        avg_win = 0.03   # 3% average win
        avg_loss = 0.02  # 2% average loss
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        
        # Adjust by confidence
        adjusted_fraction = kelly_fraction * confidence
        
        # Calculate position value
        position_value = self.portfolio_value * adjusted_fraction
        shares = int(position_value / price)
        
        return shares
    
    def execute_trade(self, symbol, signal, confidence, price):
        """Execute trade with risk management"""
        if signal == 0:
            return False
        
        # Calculate position size
        shares = self.calculate_position_size(symbol, confidence, price)
        
        if shares == 0:
            return False
        
        # Simulate slippage and commission
        slippage = 0.001 * abs(signal)  # 0.1% slippage
        commission = max(1.0, shares * price * 0.0005)  # Commission
        
        if signal > 0:  # Buy
            total_cost = shares * price * (1 + slippage) + commission
            if total_cost <= self.portfolio_value * 0.95:  # Keep 5% cash
                self.positions[symbol] = self.positions.get(symbol, 0) + shares
                self.portfolio_value -= total_cost
                
                trade = {
                    'symbol': symbol,
                    'action': 'BUY',
                    'shares': shares,
                    'price': price,
                    'total_cost': total_cost,
                    'timestamp': datetime.now()
                }
                self.trades.append(trade)
                self.trades_executed += 1
                return True
        
        else:  # Sell
            current_position = self.positions.get(symbol, 0)
            if current_position > 0:
                shares_to_sell = min(shares, current_position)
                proceeds = shares_to_sell * price * (1 - slippage) - commission
                
                self.positions[symbol] = current_position - shares_to_sell
                self.portfolio_value += proceeds
                
                if self.positions[symbol] == 0:
                    del self.positions[symbol]
                
                trade = {
                    'symbol': symbol,
                    'action': 'SELL',
                    'shares': shares_to_sell,
                    'price': price,
                    'proceeds': proceeds,
                    'timestamp': datetime.now()
                }
                self.trades.append(trade)
                self.trades_executed += 1
                return True
        
        return False
    
    def calculate_portfolio_value(self, current_prices):
        """Calculate current portfolio value"""
        total_value = self.portfolio_value  # Cash
        
        for symbol, shares in self.positions.items():
            if symbol in current_prices:
                total_value += shares * current_prices[symbol]
        
        return total_value
    
    def run_simulation(self, symbols=['AAPL', 'MSFT', 'GOOGL'], days=100):
        """Run trading simulation"""
        print("=" * 60)
        print("QUANTITATIVE TRADING SYSTEM DEMONSTRATION")
        print("=" * 60)
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Trading Symbols: {', '.join(symbols)}")
        print(f"Simulation Period: {days} days")
        print("\nStarting simulation...\n")
        
        # Initialize price history
        price_history = {symbol: [100 + random.uniform(-10, 10)] for symbol in symbols}
        
        for day in range(days):
            current_prices = {}
            
            # Update prices for each symbol
            for symbol in symbols:
                new_price = self.generate_mock_price(price_history[symbol][-1])
                price_history[symbol].append(new_price)
                current_prices[symbol] = new_price
                
                # Generate and execute signals
                signal, confidence = self.generate_signal(symbol, price_history[symbol])
                
                if signal != 0 and confidence > 0.6:
                    success = self.execute_trade(symbol, signal, confidence, new_price)
                    action = "BUY" if signal > 0 else "SELL"
                    
                    if success:
                        print(f"Day {day+1:3d}: {action} {symbol} at ${new_price:.2f} "
                              f"(Confidence: {confidence:.2f})")
            
            # Update portfolio value
            current_portfolio_value = self.calculate_portfolio_value(current_prices)
            
            # Print periodic updates
            if (day + 1) % 20 == 0:
                total_return = (current_portfolio_value - self.initial_capital) / self.initial_capital
                print(f"\nDay {day+1} Update:")
                print(f"Portfolio Value: ${current_portfolio_value:,.2f}")
                print(f"Total Return: {total_return:.2%}")
                print(f"Active Positions: {len(self.positions)}")
                print("-" * 40)
        
        # Final results
        final_value = self.calculate_portfolio_value(current_prices)
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        print("\n" + "=" * 60)
        print("SIMULATION RESULTS")
        print("=" * 60)
        print(f"Initial Capital:     ${self.initial_capital:,.2f}")
        print(f"Final Value:         ${final_value:,.2f}")
        print(f"Total Return:        {total_return:.2%}")
        print(f"Total Trades:        {self.trades_executed}")
        print(f"Signals Generated:   {self.signals_generated}")
        print(f"Active Positions:    {len(self.positions)}")
        
        if self.trades_executed > 0:
            hit_ratio = len([t for t in self.trades if t.get('proceeds', 0) > t.get('total_cost', float('inf'))]) / self.trades_executed
            print(f"Win Rate:            {hit_ratio:.1%}")
        
        # Show final positions
        if self.positions:
            print("\nFinal Positions:")
            for symbol, shares in self.positions.items():
                value = shares * current_prices[symbol]
                print(f"  {symbol}: {shares} shares (${value:,.2f})")
        
        print("\n" + "=" * 60)
        print("SYSTEM COMPONENTS DEMONSTRATED:")
        print("=" * 60)
        print("✓ Real-time Data Feed (simulated)")
        print("✓ Technical Indicators (RSI, MACD, MA)")
        print("✓ Signal Generation and Confidence Scoring")
        print("✓ Risk Management and Position Sizing")
        print("✓ Trade Execution with Slippage and Commission")
        print("✓ Portfolio Management and Tracking")
        print("✓ Performance Metrics Calculation")
        print("\nFull system includes:")
        print("• Advanced Mathematical Models (Black-Scholes, GARCH, Kalman)")
        print("• Machine Learning Signal Generation")
        print("• Professional Execution Algorithms (TWAP, VWAP)")
        print("• Comprehensive Backtesting Framework")
        print("• Monte Carlo Simulation and Walk-Forward Analysis")
        print("• VaR and Advanced Risk Metrics")

def main():
    """Run the demonstration"""
    demo = SimpleDemo()
    demo.run_simulation()

if __name__ == "__main__":
    main()