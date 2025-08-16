import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from enum import Enum
import asyncio
import logging
from threading import Thread, Lock
import queue
import time

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class Order:
    """Order data structure"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float = None
    stop_price: float = None
    time_in_force: str = "DAY"
    timestamp: datetime = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class Fill:
    """Trade fill data structure"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    timestamp: datetime
    commission: float = 0.0

class SlippageModel:
    """Model for calculating realistic slippage"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.base_slippage = self.config.get('base_slippage', 0.0005)  # 5 bps
        self.volume_impact = self.config.get('volume_impact', 0.1)
        self.volatility_impact = self.config.get('volatility_impact', 0.5)
        
    def calculate_slippage(self, order: Order, market_data: dict, 
                          order_book: dict = None) -> float:
        """Calculate expected slippage for an order"""
        
        # Base slippage
        slippage = self.base_slippage
        
        # Volume impact (larger orders have more slippage)
        if 'avg_volume' in market_data:
            volume_ratio = (order.quantity * order.price if order.price else 0) / market_data['avg_volume']
            volume_impact = self.volume_impact * np.sqrt(volume_ratio)
            slippage += volume_impact
        
        # Volatility impact (higher volatility = more slippage)
        if 'volatility' in market_data:
            vol_impact = self.volatility_impact * market_data['volatility']
            slippage += vol_impact
        
        # Market order vs limit order
        if order.order_type == OrderType.MARKET:
            slippage *= 1.5  # Market orders have higher slippage
        
        # Bid-ask spread impact
        if order_book and 'bid' in order_book and 'ask' in order_book:
            spread = (order_book['ask'] - order_book['bid']) / order_book['mid']
            slippage += spread * 0.5
        
        # Time of day impact (higher slippage during market open/close)
        hour = datetime.now().hour
        if hour in [9, 10, 15, 16]:  # Market open/close hours
            slippage *= 1.3
        
        return min(slippage, 0.01)  # Cap at 1%

class ExecutionAlgorithm:
    """Base class for execution algorithms"""
    
    def __init__(self, name: str):
        self.name = name
        
    def execute(self, order: Order, market_data: dict) -> List[Order]:
        """Execute order using this algorithm"""
        raise NotImplementedError

class TWAPAlgorithm(ExecutionAlgorithm):
    """Time-Weighted Average Price algorithm"""
    
    def __init__(self, duration_minutes: int = 30, num_slices: int = 10):
        super().__init__("TWAP")
        self.duration_minutes = duration_minutes
        self.num_slices = num_slices
        
    def execute(self, order: Order, market_data: dict) -> List[Order]:
        """Break order into time-based slices"""
        slice_size = order.quantity // self.num_slices
        remainder = order.quantity % self.num_slices
        
        child_orders = []
        slice_interval = self.duration_minutes / self.num_slices
        
        for i in range(self.num_slices):
            slice_qty = slice_size + (1 if i < remainder else 0)
            
            if slice_qty > 0:
                child_order = Order(
                    id=f"{order.id}_slice_{i}",
                    symbol=order.symbol,
                    side=order.side,
                    order_type=OrderType.LIMIT,
                    quantity=slice_qty,
                    price=order.price,
                    timestamp=order.timestamp + timedelta(minutes=i * slice_interval)
                )
                child_orders.append(child_order)
        
        return child_orders

class VWAPAlgorithm(ExecutionAlgorithm):
    """Volume-Weighted Average Price algorithm"""
    
    def __init__(self, participation_rate: float = 0.1):
        super().__init__("VWAP")
        self.participation_rate = participation_rate
        
    def execute(self, order: Order, market_data: dict) -> List[Order]:
        """Break order based on historical volume patterns"""
        # Simplified VWAP - in practice would use intraday volume curves
        volume_profile = self._get_volume_profile()
        
        child_orders = []
        remaining_qty = order.quantity
        
        for i, volume_weight in enumerate(volume_profile):
            if remaining_qty <= 0:
                break
                
            slice_qty = min(
                int(order.quantity * volume_weight),
                remaining_qty
            )
            
            if slice_qty > 0:
                child_order = Order(
                    id=f"{order.id}_vwap_{i}",
                    symbol=order.symbol,
                    side=order.side,
                    order_type=OrderType.LIMIT,
                    quantity=slice_qty,
                    price=order.price,
                    timestamp=order.timestamp + timedelta(minutes=i * 15)
                )
                child_orders.append(child_order)
                remaining_qty -= slice_qty
        
        return child_orders
    
    def _get_volume_profile(self) -> List[float]:
        """Get typical intraday volume distribution"""
        # Simplified U-shaped volume curve
        profile = [0.15, 0.08, 0.06, 0.05, 0.05, 0.05, 0.06, 0.08, 0.12, 0.15, 0.15]
        return [p / sum(profile) for p in profile]

class ImplementationShortfallAlgorithm(ExecutionAlgorithm):
    """Implementation Shortfall algorithm"""
    
    def __init__(self, urgency: float = 0.5):
        super().__init__("IS")
        self.urgency = urgency
        
    def execute(self, order: Order, market_data: dict) -> List[Order]:
        """Optimize trade-off between market impact and timing risk"""
        # Simplified IS algorithm
        volatility = market_data.get('volatility', 0.02)
        
        # Higher urgency = fewer, larger slices
        num_slices = max(1, int(10 * (1 - self.urgency)))
        slice_size = order.quantity // num_slices
        
        child_orders = []
        for i in range(num_slices):
            child_order = Order(
                id=f"{order.id}_is_{i}",
                symbol=order.symbol,
                side=order.side,
                order_type=OrderType.LIMIT,
                quantity=slice_size,
                price=order.price,
                timestamp=order.timestamp + timedelta(minutes=i * 5)
            )
            child_orders.append(child_order)
        
        return child_orders

class SmartOrderRouter:
    """Smart Order Routing for optimal execution venues"""
    
    def __init__(self):
        self.venues = {
            'NYSE': {'fee': 0.0005, 'fill_rate': 0.95, 'latency': 1},
            'NASDAQ': {'fee': 0.0003, 'fill_rate': 0.90, 'latency': 2},
            'ARCA': {'fee': 0.0004, 'fill_rate': 0.85, 'latency': 1},
            'BATS': {'fee': 0.0002, 'fill_rate': 0.80, 'latency': 3}
        }
        
    def route_order(self, order: Order, market_data: dict) -> str:
        """Select optimal venue for order execution"""
        scores = {}
        
        for venue, props in self.venues.items():
            # Score based on fees, fill rate, and latency
            score = (props['fill_rate'] * 0.5 - 
                    props['fee'] * 1000 * 0.3 - 
                    props['latency'] * 0.2)
            scores[venue] = score
        
        return max(scores, key=scores.get)

class OrderManager:
    """Manages order lifecycle and execution"""
    
    def __init__(self, slippage_model: SlippageModel, 
                 smart_router: SmartOrderRouter):
        self.orders = {}
        self.fills = []
        self.slippage_model = slippage_model
        self.smart_router = smart_router
        self.order_queue = queue.Queue()
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)
        
    def submit_order(self, order: Order) -> bool:
        """Submit order for execution"""
        with self.lock:
            self.orders[order.id] = order
            order.status = OrderStatus.SUBMITTED
            self.order_queue.put(order)
            self.logger.info(f"Order submitted: {order.id}")
            return True
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        with self.lock:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                    order.status = OrderStatus.CANCELLED
                    self.logger.info(f"Order cancelled: {order_id}")
                    return True
        return False
    
    def fill_order(self, order: Order, fill_price: float, 
                   fill_quantity: int, market_data: dict):
        """Process order fill"""
        with self.lock:
            # Calculate slippage
            if order.price:
                expected_price = order.price
            else:
                expected_price = market_data.get('last_price', fill_price)
            
            slippage = self.slippage_model.calculate_slippage(order, market_data)
            
            # Apply slippage to fill price
            if order.side == OrderSide.BUY:
                actual_fill_price = fill_price * (1 + slippage)
            else:
                actual_fill_price = fill_price * (1 - slippage)
            
            # Calculate commission (simplified)
            commission = max(1.0, fill_quantity * actual_fill_price * 0.0005)
            
            # Create fill record
            fill = Fill(
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                quantity=fill_quantity,
                price=actual_fill_price,
                timestamp=datetime.now(),
                commission=commission
            )
            self.fills.append(fill)
            
            # Update order
            order.filled_quantity += fill_quantity
            order.avg_fill_price = self._calculate_avg_fill_price(order.id)
            order.commission += commission
            order.slippage = abs(actual_fill_price - expected_price) / expected_price
            
            if order.filled_quantity >= order.quantity:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
            
            self.logger.info(f"Order filled: {order.id}, qty: {fill_quantity}, "
                           f"price: {actual_fill_price:.2f}")
    
    def _calculate_avg_fill_price(self, order_id: str) -> float:
        """Calculate average fill price for order"""
        order_fills = [f for f in self.fills if f.order_id == order_id]
        if not order_fills:
            return 0.0
        
        total_value = sum(f.quantity * f.price for f in order_fills)
        total_quantity = sum(f.quantity for f in order_fills)
        
        return total_value / total_quantity if total_quantity > 0 else 0.0
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get current order status"""
        return self.orders.get(order_id)
    
    def get_fills(self, symbol: str = None) -> List[Fill]:
        """Get fill history"""
        if symbol:
            return [f for f in self.fills if f.symbol == symbol]
        return self.fills.copy()

class ExecutionEngine:
    """Main execution engine orchestrating all components"""
    
    def __init__(self, config):
        self.config = config
        self.slippage_model = SlippageModel(config.__dict__)
        self.smart_router = SmartOrderRouter()
        self.order_manager = OrderManager(self.slippage_model, self.smart_router)
        
        # Execution algorithms
        self.algorithms = {
            'TWAP': TWAPAlgorithm(),
            'VWAP': VWAPAlgorithm(),
            'IS': ImplementationShortfallAlgorithm()
        }
        
        self.running = False
        self.execution_thread = None
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start the execution engine"""
        self.running = True
        self.execution_thread = Thread(target=self._execution_loop, daemon=True)
        self.execution_thread.start()
        self.logger.info("Execution engine started")
    
    def stop(self):
        """Stop the execution engine"""
        self.running = False
        if self.execution_thread:
            self.execution_thread.join()
        self.logger.info("Execution engine stopped")
    
    def submit_order(self, symbol: str, side: str, quantity: int, 
                    order_type: str = "MARKET", price: float = None,
                    algorithm: str = None) -> str:
        """Submit order for execution"""
        
        order_id = f"{symbol}_{int(time.time() * 1000)}"
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=OrderSide(side.upper()),
            order_type=OrderType(order_type.upper()),
            quantity=quantity,
            price=price
        )
        
        # Use execution algorithm if specified
        if algorithm and algorithm in self.algorithms:
            child_orders = self.algorithms[algorithm].execute(order, {})
            for child_order in child_orders:
                self.order_manager.submit_order(child_order)
        else:
            self.order_manager.submit_order(order)
        
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        return self.order_manager.cancel_order(order_id)
    
    def _execution_loop(self):
        """Main execution loop"""
        while self.running:
            try:
                # Process order queue
                while not self.order_manager.order_queue.empty():
                    order = self.order_manager.order_queue.get()
                    self._process_order(order)
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
    
    def _process_order(self, order: Order):
        """Process individual order"""
        try:
            # Simulate market data (in real implementation, get from data feed)
            market_data = self._get_market_data(order.symbol)
            
            # Route order to best venue
            venue = self.smart_router.route_order(order, market_data)
            
            # Simulate order execution
            self._simulate_execution(order, market_data, venue)
            
        except Exception as e:
            self.logger.error(f"Error processing order {order.id}: {e}")
            order.status = OrderStatus.REJECTED
    
    def _get_market_data(self, symbol: str) -> dict:
        """Get current market data (simulation)"""
        # In real implementation, this would interface with data feed
        return {
            'last_price': 100.0 + np.random.normal(0, 2),
            'bid': 99.95,
            'ask': 100.05,
            'mid': 100.0,
            'volume': 1000000,
            'avg_volume': 5000000,
            'volatility': 0.02
        }
    
    def _simulate_execution(self, order: Order, market_data: dict, venue: str):
        """Simulate order execution"""
        
        # Determine fill price
        if order.order_type == OrderType.MARKET:
            fill_price = market_data['ask'] if order.side == OrderSide.BUY else market_data['bid']
        else:
            fill_price = order.price or market_data['last_price']
        
        # Simulate partial fills for large orders
        remaining_qty = order.quantity - order.filled_quantity
        
        if remaining_qty > 0:
            # Fill percentage based on market conditions
            fill_rate = 0.8 + np.random.uniform(0, 0.2)
            fill_qty = min(remaining_qty, int(remaining_qty * fill_rate))
            
            if fill_qty > 0:
                self.order_manager.fill_order(order, fill_price, fill_qty, market_data)
    
    def get_execution_report(self) -> dict:
        """Generate execution performance report"""
        fills = self.order_manager.get_fills()
        
        if not fills:
            return {'message': 'No fills to report'}
        
        total_volume = sum(f.quantity * f.price for f in fills)
        total_commission = sum(f.commission for f in fills)
        
        # Calculate VWAP
        vwap = total_volume / sum(f.quantity for f in fills) if fills else 0
        
        # Calculate average slippage
        orders = list(self.order_manager.orders.values())
        avg_slippage = np.mean([o.slippage for o in orders if o.slippage > 0])
        
        return {
            'total_fills': len(fills),
            'total_volume': total_volume,
            'total_commission': total_commission,
            'vwap': vwap,
            'avg_slippage': avg_slippage,
            'fill_rate': len([o for o in orders if o.status == OrderStatus.FILLED]) / len(orders)
        }
    
    def get_order_book(self) -> dict:
        """Get current order book snapshot"""
        active_orders = {
            oid: order for oid, order in self.order_manager.orders.items()
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
        }
        
        return {
            'active_orders': len(active_orders),
            'orders': list(active_orders.values())
        }

# Portfolio Integration Layer
class PortfolioExecutor:
    """High-level interface for portfolio management"""
    
    def __init__(self, execution_engine: ExecutionEngine, risk_manager):
        self.execution_engine = execution_engine
        self.risk_manager = risk_manager
        self.positions = {}
        self.pending_orders = {}
        self.logger = logging.getLogger(__name__)
        
    def execute_signal(self, symbol: str, signal: int, confidence: float,
                      current_price: float, volatility: float) -> bool:
        """Execute trading signal with risk management"""
        
        try:
            # Get historical returns for position sizing
            historical_returns = np.random.normal(0.001, 0.02, 100)  # Placeholder
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                symbol, confidence, current_price, volatility, historical_returns
            )
            
            if position_size == 0:
                self.logger.info(f"Position size is 0 for {symbol}, skipping trade")
                return False
            
            # Determine action based on signal and current position
            current_position = self.positions.get(symbol, 0)
            
            if signal > 0 and current_position <= 0:
                # Buy signal
                action = "BUY"
                quantity = position_size + abs(current_position)  # Cover short + go long
            elif signal < 0 and current_position >= 0:
                # Sell signal
                action = "SELL"
                quantity = position_size + abs(current_position)  # Close long + go short
            else:
                self.logger.info(f"No action needed for {symbol}")
                return False
            
            # Risk check before trade
            can_trade, risk_warnings = self.risk_manager.check_risk_before_trade(
                symbol, action, quantity, current_price
            )
            
            if not can_trade:
                self.logger.warning(f"Trade blocked by risk management: {risk_warnings}")
                return False
            
            # Calculate stop loss and take profit
            signal_direction = 1 if signal > 0 else -1
            stop_price, _ = self.risk_manager.calculate_stop_loss(
                current_price, volatility, signal_direction
            )
            tp_price, _ = self.risk_manager.calculate_take_profit(
                current_price, volatility, signal_direction
            )
            
            # Submit main order
            order_id = self.execution_engine.submit_order(
                symbol=symbol,
                side=action,
                quantity=quantity,
                order_type="MARKET"
            )
            
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'expected_position': position_size if signal > 0 else -position_size,
                'stop_price': stop_price,
                'tp_price': tp_price
            }
            
            self.logger.info(f"Order submitted: {order_id} for {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing signal for {symbol}: {e}")
            return False
    
    def update_positions(self):
        """Update position tracking based on fills"""
        fills = self.execution_engine.order_manager.get_fills()
        
        # Rebuild positions from fills
        positions = {}
        for fill in fills:
            if fill.symbol not in positions:
                positions[fill.symbol] = 0
            
            if fill.side == OrderSide.BUY:
                positions[fill.symbol] += fill.quantity
            else:
                positions[fill.symbol] -= fill.quantity
        
        self.positions = positions
    
    def get_portfolio_summary(self) -> dict:
        """Get portfolio summary with P&L"""
        self.update_positions()
        
        summary = {
            'positions': self.positions.copy(),
            'pending_orders': len(self.pending_orders),
            'total_fills': len(self.execution_engine.order_manager.get_fills()),
            'execution_stats': self.execution_engine.get_execution_report()
        }
        
        return summary

# Example usage
if __name__ == "__main__":
    from config import config
    from risk_management import RiskManager
    
    logging.basicConfig(level=logging.INFO)
    
    # Initialize components
    execution_engine = ExecutionEngine(config)
    risk_manager = RiskManager(config)
    portfolio_executor = PortfolioExecutor(execution_engine, risk_manager)
    
    # Start execution engine
    execution_engine.start()
    
    print("Execution Engine Test")
    print("=" * 30)
    
    try:
        # Simulate trading signals
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in symbols:
            signal = np.random.choice([-1, 0, 1])
            confidence = np.random.uniform(0.5, 1.0)
            price = 100 + np.random.uniform(-10, 10)
            volatility = np.random.uniform(0.1, 0.3)
            
            success = portfolio_executor.execute_signal(
                symbol, signal, confidence, price, volatility
            )
            
            print(f"{symbol}: Signal={signal}, Success={success}")
        
        # Wait for execution
        time.sleep(5)
        
        # Get portfolio summary
        summary = portfolio_executor.get_portfolio_summary()
        print("\nPortfolio Summary:")
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        # Get execution report
        exec_report = execution_engine.get_execution_report()
        print("\nExecution Report:")
        for key, value in exec_report.items():
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")
        
    finally:
        execution_engine.stop()
    
    print("\nExecution engine test completed!")