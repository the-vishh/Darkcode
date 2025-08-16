import numpy as np
import pandas as pd
import talib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

class TechnicalIndicators:
    """Advanced technical indicators for signal generation"""
    
    @staticmethod
    def rsi(prices, period=14):
        """Relative Strength Index"""
        return talib.RSI(prices, timeperiod=period)
    
    @staticmethod
    def macd(prices, fast=12, slow=26, signal=9):
        """Moving Average Convergence Divergence"""
        macd_line, macd_signal, macd_hist = talib.MACD(prices, 
                                                       fastperiod=fast, 
                                                       slowperiod=slow, 
                                                       signalperiod=signal)
        return macd_line, macd_signal, macd_hist
    
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """Bollinger Bands"""
        upper, middle, lower = talib.BBANDS(prices, 
                                           timeperiod=period, 
                                           nbdevup=std_dev, 
                                           nbdevdn=std_dev)
        return upper, middle, lower
    
    @staticmethod
    def stochastic(high, low, close, k_period=14, d_period=3):
        """Stochastic Oscillator"""
        slowk, slowd = talib.STOCH(high, low, close, 
                                  fastk_period=k_period, 
                                  slowk_period=d_period, 
                                  slowd_period=d_period)
        return slowk, slowd
    
    @staticmethod
    def atr(high, low, close, period=14):
        """Average True Range"""
        return talib.ATR(high, low, close, timeperiod=period)
    
    @staticmethod
    def adx(high, low, close, period=14):
        """Average Directional Index"""
        return talib.ADX(high, low, close, timeperiod=period)
    
    @staticmethod
    def williams_r(high, low, close, period=14):
        """Williams %R"""
        return talib.WILLR(high, low, close, timeperiod=period)
    
    @staticmethod
    def cci(high, low, close, period=20):
        """Commodity Channel Index"""
        return talib.CCI(high, low, close, timeperiod=period)
    
    @staticmethod
    def obv(close, volume):
        """On-Balance Volume"""
        return talib.OBV(close, volume)
    
    @staticmethod
    def momentum(prices, period=10):
        """Price Momentum"""
        return talib.MOM(prices, timeperiod=period)
    
    @staticmethod
    def rate_of_change(prices, period=10):
        """Rate of Change"""
        return talib.ROC(prices, timeperiod=period)
    
    @staticmethod
    def trix(prices, period=14):
        """TRIX - Triple Exponential Average"""
        return talib.TRIX(prices, timeperiod=period)
    
    @staticmethod
    def ultimate_oscillator(high, low, close, period1=7, period2=14, period3=28):
        """Ultimate Oscillator"""
        return talib.ULTOSC(high, low, close, 
                           timeperiod1=period1, 
                           timeperiod2=period2, 
                           timeperiod3=period3)

class CustomIndicators:
    """Custom technical indicators"""
    
    @staticmethod
    def hurst_exponent(prices, window=100):
        """Rolling Hurst Exponent"""
        def calculate_hurst(ts):
            if len(ts) < 10:
                return 0.5
            
            lags = range(2, min(20, len(ts)//2))
            tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
            
            try:
                poly = np.polyfit(np.log(lags), np.log(tau), 1)
                return poly[0] * 2.0
            except:
                return 0.5
        
        hurst_values = []
        for i in range(len(prices)):
            if i < window:
                hurst_values.append(0.5)
            else:
                window_data = prices[i-window:i]
                hurst_values.append(calculate_hurst(window_data))
        
        return np.array(hurst_values)
    
    @staticmethod
    def fractal_dimension(prices, window=50):
        """Fractal Dimension indicator"""
        def calc_fd(series):
            if len(series) < 3:
                return 1.5
            
            n = len(series)
            l = []
            
            for k in range(1, n//2):
                sum_val = 0
                for i in range(k, n - k):
                    sum_val += abs(series[i + k] - series[i - k])
                l.append(sum_val / (2 * k * (n - 2 * k)))
            
            if len(l) < 2:
                return 1.5
            
            try:
                x = np.arange(1, len(l) + 1)
                coeffs = np.polyfit(np.log(x), np.log(l), 1)
                return 2 - coeffs[0]
            except:
                return 1.5
        
        fd_values = []
        for i in range(len(prices)):
            if i < window:
                fd_values.append(1.5)
            else:
                window_data = prices[i-window:i]
                fd_values.append(calc_fd(window_data))
        
        return np.array(fd_values)
    
    @staticmethod
    def regime_detection(returns, window=60):
        """Regime detection based on volatility clustering"""
        vol = pd.Series(returns).rolling(window=20).std()
        vol_ma = vol.rolling(window=window).mean()
        
        regime = np.where(vol > vol_ma * 1.2, 1,  # High vol regime
                         np.where(vol < vol_ma * 0.8, -1, 0))  # Low vol regime
        
        return regime
    
    @staticmethod
    def market_efficiency_ratio(prices, period=20):
        """Kaufman's Efficiency Ratio"""
        changes = np.abs(np.diff(prices))
        net_change = np.abs(prices[period:] - prices[:-period])
        sum_changes = pd.Series(changes).rolling(window=period-1).sum()
        
        efficiency_ratio = net_change / sum_changes.values
        efficiency_ratio = np.nan_to_num(efficiency_ratio, nan=0.0)
        
        # Pad with zeros for the initial period
        result = np.zeros(len(prices))
        result[period:] = efficiency_ratio
        
        return result

class MLSignalGenerator:
    """Machine Learning based signal generation"""
    
    def __init__(self):
        self.models = {
            'rf': RandomForestClassifier(n_estimators=100, random_state=42),
            'gb': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'lr': LogisticRegression(random_state=42),
            'svm': SVC(probability=True, random_state=42)
        }
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def prepare_features(self, data):
        """Prepare features for ML models"""
        features = pd.DataFrame()
        
        # Price features
        features['returns'] = data['Close'].pct_change()
        features['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))
        features['price_ma_ratio'] = data['Close'] / data['Close'].rolling(20).mean()
        
        # Volatility features
        features['volatility'] = features['returns'].rolling(20).std()
        features['vol_ratio'] = features['volatility'] / features['volatility'].rolling(60).mean()
        
        # Volume features
        features['volume_ma_ratio'] = data['Volume'] / data['Volume'].rolling(20).mean()
        features['price_volume'] = data['Close'] * data['Volume']
        
        # Technical indicators
        features['rsi'] = TechnicalIndicators.rsi(data['Close'].values)
        macd_line, macd_signal, macd_hist = TechnicalIndicators.macd(data['Close'].values)
        features['macd'] = macd_line
        features['macd_signal'] = macd_signal
        features['macd_hist'] = macd_hist
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(data['Close'].values)
        features['bb_position'] = (data['Close'] - bb_lower) / (bb_upper - bb_lower)
        
        # Momentum indicators
        features['momentum'] = TechnicalIndicators.momentum(data['Close'].values)
        features['roc'] = TechnicalIndicators.rate_of_change(data['Close'].values)
        
        # Custom indicators
        features['hurst'] = CustomIndicators.hurst_exponent(data['Close'].values)
        features['fractal_dim'] = CustomIndicators.fractal_dimension(data['Close'].values)
        features['efficiency_ratio'] = CustomIndicators.market_efficiency_ratio(data['Close'].values)
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            features[f'return_lag_{lag}'] = features['returns'].shift(lag)
            features[f'rsi_lag_{lag}'] = features['rsi'].shift(lag)
        
        # Rolling statistics
        for window in [5, 10, 20]:
            features[f'return_mean_{window}'] = features['returns'].rolling(window).mean()
            features[f'return_std_{window}'] = features['returns'].rolling(window).std()
            features[f'rsi_mean_{window}'] = features['rsi'].rolling(window).mean()
        
        return features.fillna(0)
    
    def create_targets(self, data, horizon=5):
        """Create target variables for classification"""
        returns = data['Close'].pct_change(horizon).shift(-horizon)
        
        # Multi-class targets based on return quartiles
        targets = pd.cut(returns, bins=[-np.inf, -0.02, -0.005, 0.005, 0.02, np.inf], 
                        labels=[0, 1, 2, 3, 4])  # Strong sell, sell, hold, buy, strong buy
        
        return targets.astype(int)
    
    def train(self, data, test_size=0.3):
        """Train ML models"""
        features = self.prepare_features(data)
        targets = self.create_targets(data)
        
        # Remove rows with NaN targets
        valid_idx = ~targets.isna()
        features = features[valid_idx]
        targets = targets[valid_idx]
        
        if len(features) < 100:
            raise ValueError("Insufficient data for training")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, targets, test_size=test_size, random_state=42, stratify=targets
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models
        results = {}
        for name, model in self.models.items():
            try:
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                results[name] = accuracy
                print(f"{name.upper()} Accuracy: {accuracy:.3f}")
            except Exception as e:
                print(f"Error training {name}: {e}")
                results[name] = 0
        
        self.is_fitted = True
        return results
    
    def predict(self, data):
        """Generate predictions from trained models"""
        if not self.is_fitted:
            raise ValueError("Models must be trained before prediction")
        
        features = self.prepare_features(data)
        features_scaled = self.scaler.transform(features.tail(1))
        
        predictions = {}
        probabilities = {}
        
        for name, model in self.models.items():
            try:
                pred = model.predict(features_scaled)[0]
                prob = model.predict_proba(features_scaled)[0]
                predictions[name] = pred
                probabilities[name] = prob
            except Exception as e:
                print(f"Error predicting with {name}: {e}")
                predictions[name] = 2  # Neutral
                probabilities[name] = [0.2, 0.2, 0.2, 0.2, 0.2]
        
        return predictions, probabilities

class SignalCombiner:
    """Combine multiple signals into final trading signals"""
    
    def __init__(self, weights=None):
        self.weights = weights or {
            'technical': 0.4,
            'ml': 0.4,
            'momentum': 0.2
        }
    
    def generate_technical_signals(self, data):
        """Generate signals from technical indicators"""
        signals = pd.DataFrame(index=data.index)
        
        # RSI signals
        rsi = TechnicalIndicators.rsi(data['Close'].values)
        signals['rsi_signal'] = np.where(rsi < 30, 1,  # Oversold - Buy
                                np.where(rsi > 70, -1, 0))  # Overbought - Sell
        
        # MACD signals
        macd_line, macd_signal, macd_hist = TechnicalIndicators.macd(data['Close'].values)
        signals['macd_signal'] = np.where(macd_line > macd_signal, 1, -1)
        
        # Bollinger Bands signals
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(data['Close'].values)
        bb_position = (data['Close'] - bb_lower) / (bb_upper - bb_lower)
        signals['bb_signal'] = np.where(bb_position < 0.2, 1,  # Near lower band - Buy
                               np.where(bb_position > 0.8, -1, 0))  # Near upper band - Sell
        
        # Moving average crossover
        sma_20 = data['Close'].rolling(20).mean()
        sma_50 = data['Close'].rolling(50).mean()
        signals['ma_signal'] = np.where(sma_20 > sma_50, 1, -1)
        
        # Stochastic signals
        stoch_k, stoch_d = TechnicalIndicators.stochastic(data['High'].values, 
                                                         data['Low'].values, 
                                                         data['Close'].values)
        signals['stoch_signal'] = np.where((stoch_k < 20) & (stoch_k > stoch_d), 1,
                                  np.where((stoch_k > 80) & (stoch_k < stoch_d), -1, 0))
        
        # Combine technical signals
        technical_cols = ['rsi_signal', 'macd_signal', 'bb_signal', 'ma_signal', 'stoch_signal']
        signals['technical_combined'] = signals[technical_cols].mean(axis=1)
        
        return signals
    
    def generate_momentum_signals(self, data):
        """Generate momentum-based signals"""
        signals = pd.DataFrame(index=data.index)
        
        # Price momentum
        returns = data['Close'].pct_change()
        mom_5 = returns.rolling(5).mean()
        mom_20 = returns.rolling(20).mean()
        
        signals['momentum_signal'] = np.where(mom_5 > mom_20, 1, -1)
        
        # Volume momentum
        volume_sma = data['Volume'].rolling(20).mean()
        volume_ratio = data['Volume'] / volume_sma
        
        # Strong momentum with volume confirmation
        signals['volume_momentum'] = np.where((mom_5 > 0) & (volume_ratio > 1.2), 1,
                                     np.where((mom_5 < 0) & (volume_ratio > 1.2), -1, 0))
        
        # Combine momentum signals
        signals['momentum_combined'] = (signals['momentum_signal'] + signals['volume_momentum']) / 2
        
        return signals
    
    def combine_signals(self, technical_signals, ml_predictions, momentum_signals):
        """Combine all signals with weights"""
        # Convert ML predictions to signal format (-1, 0, 1)
        ml_signal = 0
        if ml_predictions:
            # Average predictions across models
            avg_pred = np.mean([pred for pred in ml_predictions.values()])
            if avg_pred >= 3.5:  # Strong buy
                ml_signal = 1
            elif avg_pred <= 1.5:  # Strong sell
                ml_signal = -1
            else:
                ml_signal = 0
        
        # Get latest signals
        tech_signal = technical_signals['technical_combined'].iloc[-1] if not technical_signals.empty else 0
        mom_signal = momentum_signals['momentum_combined'].iloc[-1] if not momentum_signals.empty else 0
        
        # Weighted combination
        final_signal = (self.weights['technical'] * tech_signal + 
                       self.weights['ml'] * ml_signal + 
                       self.weights['momentum'] * mom_signal)
        
        # Convert to discrete signal
        if final_signal > 0.3:
            return 1  # Buy
        elif final_signal < -0.3:
            return -1  # Sell
        else:
            return 0  # Hold
    
    def generate_confidence_score(self, technical_signals, ml_probabilities, momentum_signals):
        """Generate confidence score for the signal"""
        confidence_factors = []
        
        # Technical indicator agreement
        if not technical_signals.empty:
            latest_signals = technical_signals[['rsi_signal', 'macd_signal', 'bb_signal', 
                                              'ma_signal', 'stoch_signal']].iloc[-1]
            agreement = np.abs(latest_signals.mean())
            confidence_factors.append(agreement)
        
        # ML model confidence (entropy-based)
        if ml_probabilities:
            for model_probs in ml_probabilities.values():
                entropy = -np.sum(model_probs * np.log(model_probs + 1e-10))
                max_entropy = np.log(len(model_probs))
                confidence = 1 - (entropy / max_entropy)
                confidence_factors.append(confidence)
        
        # Momentum strength
        if not momentum_signals.empty:
            mom_strength = np.abs(momentum_signals['momentum_combined'].iloc[-1])
            confidence_factors.append(mom_strength)
        
        # Overall confidence
        return np.mean(confidence_factors) if confidence_factors else 0.5

class SignalGenerator:
    """Main signal generation class"""
    
    def __init__(self, config=None):
        self.technical = TechnicalIndicators()
        self.custom = CustomIndicators()
        self.ml_generator = MLSignalGenerator()
        self.combiner = SignalCombiner()
        self.config = config
        
    def generate_signals(self, data, train_ml=True):
        """Generate comprehensive trading signals"""
        results = {
            'signal': 0,
            'confidence': 0.5,
            'technical_signals': {},
            'ml_predictions': {},
            'ml_probabilities': {},
            'momentum_signals': {},
            'indicators': {}
        }
        
        try:
            # Generate technical signals
            technical_signals = self.combiner.generate_technical_signals(data)
            results['technical_signals'] = technical_signals.to_dict('records')[-1] if not technical_signals.empty else {}
            
            # Generate momentum signals
            momentum_signals = self.combiner.generate_momentum_signals(data)
            results['momentum_signals'] = momentum_signals.to_dict('records')[-1] if not momentum_signals.empty else {}
            
            # Train and generate ML signals
            ml_predictions = {}
            ml_probabilities = {}
            
            if train_ml and len(data) > 100:
                try:
                    self.ml_generator.train(data)
                    ml_predictions, ml_probabilities = self.ml_generator.predict(data)
                except Exception as e:
                    print(f"ML training/prediction error: {e}")
            
            results['ml_predictions'] = ml_predictions
            results['ml_probabilities'] = ml_probabilities
            
            # Combine signals
            final_signal = self.combiner.combine_signals(technical_signals, ml_predictions, momentum_signals)
            confidence = self.combiner.generate_confidence_score(technical_signals, ml_probabilities, momentum_signals)
            
            results['signal'] = final_signal
            results['confidence'] = confidence
            
            # Add key indicators for reference
            if len(data) > 0:
                latest_price = data['Close'].iloc[-1]
                results['indicators'] = {
                    'price': latest_price,
                    'rsi': TechnicalIndicators.rsi(data['Close'].values)[-1] if len(data) >= 14 else 50,
                    'macd': TechnicalIndicators.macd(data['Close'].values)[0][-1] if len(data) >= 26 else 0,
                    'bb_position': ((latest_price - TechnicalIndicators.bollinger_bands(data['Close'].values)[2][-1]) / 
                                   (TechnicalIndicators.bollinger_bands(data['Close'].values)[0][-1] - 
                                    TechnicalIndicators.bollinger_bands(data['Close'].values)[2][-1])) if len(data) >= 20 else 0.5
                }
            
        except Exception as e:
            print(f"Error generating signals: {e}")
            
        return results

# Example usage
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    
    # Simulate realistic stock data
    returns = np.random.normal(0.001, 0.02, 1000)
    prices = 100 * np.exp(np.cumsum(returns))
    volumes = np.random.lognormal(10, 0.5, 1000)
    
    data = pd.DataFrame({
        'Date': dates,
        'Close': prices,
        'High': prices * (1 + np.random.uniform(0, 0.02, 1000)),
        'Low': prices * (1 - np.random.uniform(0, 0.02, 1000)),
        'Volume': volumes
    })
    data['Open'] = data['Close'].shift(1).fillna(data['Close'])
    data.set_index('Date', inplace=True)
    
    # Generate signals
    signal_gen = SignalGenerator()
    signals = signal_gen.generate_signals(data)
    
    print("Signal Generation Results:")
    print("=" * 40)
    print(f"Final Signal: {signals['signal']}")
    print(f"Confidence: {signals['confidence']:.3f}")
    print(f"Current Price: ${signals['indicators']['price']:.2f}")
    print(f"RSI: {signals['indicators']['rsi']:.1f}")
    print(f"MACD: {signals['indicators']['macd']:.4f}")
    print(f"BB Position: {signals['indicators']['bb_position']:.3f}")
    
    # Signal interpretation
    signal_names = {-1: "SELL", 0: "HOLD", 1: "BUY"}
    print(f"\nRecommendation: {signal_names[signals['signal']]}")
    print(f"Confidence Level: {'High' if signals['confidence'] > 0.7 else 'Medium' if signals['confidence'] > 0.5 else 'Low'}")