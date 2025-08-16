import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class VaRCalculator:
    """Value at Risk calculation methods"""
    
    @staticmethod
    def historical_var(returns, confidence=0.95, window=252):
        """Historical Value at Risk"""
        if len(returns) < window:
            return np.percentile(returns, (1 - confidence) * 100)
        
        # Use rolling window for dynamic VaR
        var_series = []
        for i in range(window, len(returns) + 1):
            window_returns = returns[i-window:i]
            var_value = np.percentile(window_returns, (1 - confidence) * 100)
            var_series.append(var_value)
        
        return var_series[-1] if var_series else np.percentile(returns, (1 - confidence) * 100)
    
    @staticmethod
    def parametric_var(returns, confidence=0.95):
        """Parametric (Normal) VaR"""
        mean = np.mean(returns)
        std = np.std(returns)
        z_score = stats.norm.ppf(1 - confidence)
        return mean + z_score * std
    
    @staticmethod
    def cornish_fisher_var(returns, confidence=0.95):
        """Cornish-Fisher VaR (accounts for skewness and kurtosis)"""
        mean = np.mean(returns)
        std = np.std(returns)
        skew = stats.skew(returns)
        kurt = stats.kurtosis(returns)
        
        z = stats.norm.ppf(1 - confidence)
        
        # Cornish-Fisher adjustment
        z_cf = (z + 
                (z**2 - 1) * skew / 6 + 
                (z**3 - 3*z) * kurt / 24 - 
                (2*z**3 - 5*z) * skew**2 / 36)
        
        return mean + z_cf * std
    
    @staticmethod
    def conditional_var(returns, confidence=0.95):
        """Conditional VaR (Expected Shortfall)"""
        var = VaRCalculator.historical_var(returns, confidence)
        tail_returns = returns[returns <= var]
        return np.mean(tail_returns) if len(tail_returns) > 0 else var

class PositionSizing:
    """Position sizing algorithms"""
    
    @staticmethod
    def fixed_fractional(capital, risk_per_trade=0.02):
        """Fixed fractional position sizing"""
        return capital * risk_per_trade
    
    @staticmethod
    def kelly_criterion(returns, confidence=0.6):
        """Kelly Criterion position sizing"""
        if len(returns) < 10:
            return 0.1  # Conservative default
        
        # Calculate win rate and average win/loss
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        if len(wins) == 0 or len(losses) == 0:
            return 0.1
        
        win_rate = len(wins) / len(returns)
        avg_win = np.mean(wins)
        avg_loss = np.abs(np.mean(losses))
        
        if avg_loss == 0:
            return 0.1
        
        # Kelly formula: f = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
        b = avg_win / avg_loss
        kelly_fraction = (b * win_rate - (1 - win_rate)) / b
        
        # Cap Kelly fraction to prevent over-leveraging
        return max(0, min(kelly_fraction * confidence, 0.25))
    
    @staticmethod
    def optimal_f(returns):
        """Optimal f position sizing"""
        def objective(f):
            if f <= 0 or f >= 1:
                return -np.inf
            
            # Calculate geometric mean return
            portfolio_returns = 1 + f * np.array(returns)
            
            # Avoid log of negative numbers
            if np.any(portfolio_returns <= 0):
                return -np.inf
            
            return -np.prod(portfolio_returns) ** (1/len(returns))
        
        try:
            result = minimize(objective, 0.1, bounds=[(0.01, 0.5)], method='L-BFGS-B')
            return result.x[0] if result.success else 0.1
        except:
            return 0.1
    
    @staticmethod
    def volatility_adjusted(capital, volatility, target_vol=0.15):
        """Volatility-adjusted position sizing"""
        if volatility <= 0:
            return capital * 0.1
        
        vol_adjustment = target_vol / volatility
        return capital * min(vol_adjustment, 0.3)  # Cap at 30%

class DrawdownAnalyzer:
    """Drawdown analysis and control"""
    
    @staticmethod
    def calculate_drawdowns(equity_curve):
        """Calculate drawdown series"""
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        return drawdown
    
    @staticmethod
    def max_drawdown(equity_curve):
        """Maximum drawdown"""
        drawdowns = DrawdownAnalyzer.calculate_drawdowns(equity_curve)
        return np.min(drawdowns)
    
    @staticmethod
    def current_drawdown(equity_curve):
        """Current drawdown"""
        if len(equity_curve) == 0:
            return 0
        
        peak = np.max(equity_curve)
        current = equity_curve[-1]
        return (current - peak) / peak
    
    @staticmethod
    def underwater_curve(equity_curve):
        """Underwater curve (drawdown over time)"""
        return DrawdownAnalyzer.calculate_drawdowns(equity_curve)
    
    @staticmethod
    def recovery_factor(equity_curve):
        """Recovery factor (total return / max drawdown)"""
        if len(equity_curve) < 2:
            return 0
        
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        max_dd = abs(DrawdownAnalyzer.max_drawdown(equity_curve))
        
        return total_return / max_dd if max_dd != 0 else np.inf

class PortfolioRisk:
    """Portfolio-level risk management"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.positions = {}
        self.equity_history = [initial_capital]
        self.returns_history = []
        
    def add_position(self, symbol, quantity, price, timestamp):
        """Add a position to the portfolio"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'total_cost': 0
            }
        
        pos = self.positions[symbol]
        
        # Update position
        new_total_cost = pos['total_cost'] + quantity * price
        new_quantity = pos['quantity'] + quantity
        
        if new_quantity != 0:
            pos['avg_price'] = new_total_cost / new_quantity
        else:
            pos['avg_price'] = 0
            new_total_cost = 0
        
        pos['quantity'] = new_quantity
        pos['total_cost'] = new_total_cost
        
        # Clean up zero positions
        if pos['quantity'] == 0:
            del self.positions[symbol]
    
    def get_portfolio_value(self, current_prices):
        """Calculate current portfolio value"""
        cash = self.initial_capital
        
        # Subtract costs of current positions
        for symbol, pos in self.positions.items():
            cash -= pos['total_cost']
        
        # Add current market value
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                cash += pos['quantity'] * current_prices[symbol]
        
        return max(cash, 0)
    
    def calculate_portfolio_var(self, returns_matrix, confidence=0.95):
        """Calculate portfolio VaR using correlation matrix"""
        if len(returns_matrix.columns) < 2:
            return 0
        
        # Get portfolio weights
        symbols = list(self.positions.keys())
        if not symbols:
            return 0
        
        weights = []
        total_value = sum(pos['quantity'] * pos['avg_price'] 
                         for pos in self.positions.values())
        
        if total_value == 0:
            return 0
        
        for symbol in symbols:
            if symbol in returns_matrix.columns:
                weight = (self.positions[symbol]['quantity'] * 
                         self.positions[symbol]['avg_price']) / total_value
                weights.append(weight)
            else:
                weights.append(0)
        
        if not weights or sum(weights) == 0:
            return 0
        
        weights = np.array(weights)
        
        # Calculate portfolio volatility
        cov_matrix = returns_matrix[symbols].cov().values
        portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_vol = np.sqrt(portfolio_var)
        
        # VaR calculation
        z_score = stats.norm.ppf(1 - confidence)
        portfolio_var_estimate = z_score * portfolio_vol * np.sqrt(1)  # 1-day VaR
        
        return portfolio_var_estimate
    
    def calculate_concentration_risk(self):
        """Calculate portfolio concentration risk"""
        if not self.positions:
            return 0
        
        total_value = sum(pos['quantity'] * pos['avg_price'] 
                         for pos in self.positions.values())
        
        if total_value == 0:
            return 0
        
        weights = [(pos['quantity'] * pos['avg_price']) / total_value 
                  for pos in self.positions.values()]
        
        # Herfindahl-Hirschman Index
        hhi = sum(w**2 for w in weights)
        return hhi
    
    def check_risk_limits(self, max_position_size=0.1, max_sector_exposure=0.3, 
                         max_drawdown=0.15):
        """Check various risk limits"""
        warnings = []
        
        # Position size limits
        total_value = sum(pos['quantity'] * pos['avg_price'] 
                         for pos in self.positions.values())
        
        if total_value > 0:
            for symbol, pos in self.positions.items():
                position_weight = (pos['quantity'] * pos['avg_price']) / total_value
                if position_weight > max_position_size:
                    warnings.append(f"Position size limit exceeded for {symbol}: "
                                  f"{position_weight:.2%} > {max_position_size:.2%}")
        
        # Drawdown limit
        if len(self.equity_history) > 1:
            current_dd = DrawdownAnalyzer.current_drawdown(self.equity_history)
            if current_dd < -max_drawdown:
                warnings.append(f"Maximum drawdown exceeded: "
                              f"{current_dd:.2%} < -{max_drawdown:.2%}")
        
        # Concentration risk
        concentration = self.calculate_concentration_risk()
        if concentration > 0.5:  # Highly concentrated
            warnings.append(f"High concentration risk detected: HHI = {concentration:.3f}")
        
        return warnings

class RiskManager:
    """Main risk management class"""
    
    def __init__(self, config):
        self.config = config
        self.var_calculator = VaRCalculator()
        self.position_sizer = PositionSizing()
        self.drawdown_analyzer = DrawdownAnalyzer()
        self.portfolio_risk = PortfolioRisk(config.INITIAL_CAPITAL)
        
    def calculate_position_size(self, symbol, signal_strength, price, 
                              volatility, historical_returns):
        """Calculate optimal position size"""
        capital = self.portfolio_risk.get_portfolio_value({symbol: price})
        
        # Base position size using configured method
        if self.config.POSITION_SIZING_METHOD == 'fixed':
            base_size = self.position_sizer.fixed_fractional(
                capital, self.config.MAX_POSITION_SIZE)
        elif self.config.POSITION_SIZING_METHOD == 'kelly':
            kelly_fraction = self.position_sizer.kelly_criterion(historical_returns)
            base_size = capital * kelly_fraction
        elif self.config.POSITION_SIZING_METHOD == 'optimal_f':
            optimal_fraction = self.position_sizer.optimal_f(historical_returns)
            base_size = capital * optimal_fraction
        else:
            # Volatility adjusted
            base_size = self.position_sizer.volatility_adjusted(capital, volatility)
        
        # Adjust for signal strength
        adjusted_size = base_size * abs(signal_strength)
        
        # Apply maximum position size limit
        max_position_value = capital * self.config.MAX_POSITION_SIZE
        final_size = min(adjusted_size, max_position_value)
        
        # Convert to number of shares
        shares = int(final_size / price) if price > 0 else 0
        
        return shares
    
    def check_risk_before_trade(self, symbol, action, quantity, price):
        """Comprehensive risk check before executing trade"""
        risks = []
        
        # Current portfolio value
        current_value = self.portfolio_risk.get_portfolio_value({symbol: price})
        
        # Position size check
        trade_value = quantity * price
        position_weight = trade_value / current_value if current_value > 0 else 0
        
        if position_weight > self.config.MAX_POSITION_SIZE:
            risks.append(f"Position size exceeds limit: {position_weight:.2%}")
        
        # Drawdown check
        if len(self.portfolio_risk.equity_history) > 1:
            current_dd = DrawdownAnalyzer.current_drawdown(
                self.portfolio_risk.equity_history)
            if current_dd < -self.config.MAX_DRAWDOWN:
                risks.append(f"Portfolio in excessive drawdown: {current_dd:.2%}")
        
        # Daily loss limit
        if len(self.portfolio_risk.returns_history) > 0:
            today_return = self.portfolio_risk.returns_history[-1]
            if today_return < -self.config.MAX_DAILY_LOSS:
                risks.append(f"Daily loss limit exceeded: {today_return:.2%}")
        
        # Liquidity check (simplified)
        if trade_value > current_value * 0.5:
            risks.append("Trade size too large relative to portfolio")
        
        return len(risks) == 0, risks
    
    def calculate_stop_loss(self, entry_price, volatility, signal_direction):
        """Calculate dynamic stop loss based on volatility"""
        # Base stop loss from configuration
        base_stop = self.config.STOP_LOSS_PCT
        
        # Volatility adjustment (higher vol = wider stops)
        vol_multiplier = max(1.0, volatility / 0.02)  # Normalize to 2% base vol
        adjusted_stop = base_stop * vol_multiplier
        
        # Cap the stop loss
        final_stop = min(adjusted_stop, 0.1)  # Max 10% stop
        
        if signal_direction > 0:  # Long position
            stop_price = entry_price * (1 - final_stop)
        else:  # Short position
            stop_price = entry_price * (1 + final_stop)
        
        return stop_price, final_stop
    
    def calculate_take_profit(self, entry_price, volatility, signal_direction):
        """Calculate dynamic take profit based on volatility"""
        # Base take profit from configuration
        base_tp = self.config.TAKE_PROFIT_PCT
        
        # Volatility adjustment
        vol_multiplier = max(1.0, volatility / 0.02)
        adjusted_tp = base_tp * vol_multiplier
        
        if signal_direction > 0:  # Long position
            tp_price = entry_price * (1 + adjusted_tp)
        else:  # Short position
            tp_price = entry_price * (1 - adjusted_tp)
        
        return tp_price, adjusted_tp
    
    def update_portfolio_metrics(self, current_prices):
        """Update portfolio risk metrics"""
        current_value = self.portfolio_risk.get_portfolio_value(current_prices)
        self.portfolio_risk.equity_history.append(current_value)
        
        # Calculate return
        if len(self.portfolio_risk.equity_history) > 1:
            prev_value = self.portfolio_risk.equity_history[-2]
            daily_return = (current_value - prev_value) / prev_value
            self.portfolio_risk.returns_history.append(daily_return)
        
        # Check risk limits
        warnings = self.portfolio_risk.check_risk_limits(
            self.config.MAX_POSITION_SIZE,
            0.3,  # Max sector exposure
            self.config.MAX_DRAWDOWN
        )
        
        return {
            'portfolio_value': current_value,
            'current_drawdown': DrawdownAnalyzer.current_drawdown(
                self.portfolio_risk.equity_history),
            'max_drawdown': DrawdownAnalyzer.max_drawdown(
                self.portfolio_risk.equity_history),
            'concentration_risk': self.portfolio_risk.calculate_concentration_risk(),
            'risk_warnings': warnings
        }
    
    def get_risk_report(self, returns_data=None):
        """Generate comprehensive risk report"""
        report = {
            'portfolio_metrics': {},
            'var_metrics': {},
            'position_metrics': {},
            'drawdown_metrics': {}
        }
        
        # Portfolio metrics
        if len(self.portfolio_risk.equity_history) > 1:
            equity = np.array(self.portfolio_risk.equity_history)
            
            report['portfolio_metrics'] = {
                'total_return': (equity[-1] - equity[0]) / equity[0],
                'annualized_return': ((equity[-1] / equity[0]) ** (252/len(equity))) - 1,
                'volatility': np.std(self.portfolio_risk.returns_history) * np.sqrt(252),
                'sharpe_ratio': (np.mean(self.portfolio_risk.returns_history) * 252) / 
                               (np.std(self.portfolio_risk.returns_history) * np.sqrt(252))
            }
        
        # VaR metrics
        if len(self.portfolio_risk.returns_history) > 10:
            returns = np.array(self.portfolio_risk.returns_history)
            
            report['var_metrics'] = {
                'var_95': self.var_calculator.historical_var(returns, 0.95),
                'var_99': self.var_calculator.historical_var(returns, 0.99),
                'cvar_95': self.var_calculator.conditional_var(returns, 0.95),
                'parametric_var': self.var_calculator.parametric_var(returns, 0.95)
            }
        
        # Position metrics
        report['position_metrics'] = {
            'num_positions': len(self.portfolio_risk.positions),
            'concentration_risk': self.portfolio_risk.calculate_concentration_risk(),
            'largest_position': max([
                pos['quantity'] * pos['avg_price'] 
                for pos in self.portfolio_risk.positions.values()
            ]) if self.portfolio_risk.positions else 0
        }
        
        # Drawdown metrics
        if len(self.portfolio_risk.equity_history) > 1:
            equity = np.array(self.portfolio_risk.equity_history)
            
            report['drawdown_metrics'] = {
                'max_drawdown': DrawdownAnalyzer.max_drawdown(equity),
                'current_drawdown': DrawdownAnalyzer.current_drawdown(equity),
                'recovery_factor': DrawdownAnalyzer.recovery_factor(equity)
            }
        
        return report

# Example usage
if __name__ == "__main__":
    from config import config
    
    # Initialize risk manager
    risk_manager = RiskManager(config)
    
    # Simulate some trades
    np.random.seed(42)
    prices = {'AAPL': 150.0, 'MSFT': 300.0, 'GOOGL': 2500.0}
    returns = np.random.normal(0.001, 0.02, 100)
    
    print("Risk Management System Test")
    print("=" * 40)
    
    # Test position sizing
    position_size = risk_manager.calculate_position_size(
        'AAPL', 0.8, 150.0, 0.25, returns)
    print(f"Recommended position size for AAPL: {position_size} shares")
    
    # Test risk check
    can_trade, risk_warnings = risk_manager.check_risk_before_trade(
        'AAPL', 'BUY', position_size, 150.0)
    print(f"Can execute trade: {can_trade}")
    if risk_warnings:
        print("Risk warnings:", risk_warnings)
    
    # Test stop loss and take profit
    stop_price, stop_pct = risk_manager.calculate_stop_loss(150.0, 0.25, 1)
    tp_price, tp_pct = risk_manager.calculate_take_profit(150.0, 0.25, 1)
    print(f"Stop loss: ${stop_price:.2f} ({stop_pct:.1%})")
    print(f"Take profit: ${tp_price:.2f} ({tp_pct:.1%})")
    
    # Simulate portfolio updates
    for i in range(10):
        current_prices = {k: v * (1 + np.random.normal(0, 0.01)) 
                         for k, v in prices.items()}
        metrics = risk_manager.update_portfolio_metrics(current_prices)
    
    # Generate risk report
    risk_report = risk_manager.get_risk_report()
    print("\nRisk Report:")
    for category, metrics in risk_report.items():
        if metrics:
            print(f"\n{category.upper()}:")
            for metric, value in metrics.items():
                if isinstance(value, float):
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value}")
    
    print("\nRisk management system initialized successfully!")