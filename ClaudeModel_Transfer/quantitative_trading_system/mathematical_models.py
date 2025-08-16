import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression
from arch import arch_model
from pykalman import KalmanFilter
import warnings
warnings.filterwarnings('ignore')

class BlackScholesModel:
    """Black-Scholes option pricing model"""
    
    @staticmethod
    def call_price(S, K, T, r, sigma):
        """
        Calculate Black-Scholes call option price
        S: Current stock price
        K: Strike price
        T: Time to expiration
        r: Risk-free rate
        sigma: Volatility
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        call_price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
        return call_price
    
    @staticmethod
    def put_price(S, K, T, r, sigma):
        """Calculate Black-Scholes put option price"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        put_price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
        return put_price
    
    @staticmethod
    def delta(S, K, T, r, sigma, option_type='call'):
        """Calculate option delta (price sensitivity to underlying)"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type == 'call':
            return stats.norm.cdf(d1)
        else:
            return stats.norm.cdf(d1) - 1
    
    @staticmethod
    def gamma(S, K, T, r, sigma):
        """Calculate option gamma (delta sensitivity)"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return stats.norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    @staticmethod
    def theta(S, K, T, r, sigma, option_type='call'):
        """Calculate option theta (time decay)"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        theta_part1 = -(S * stats.norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        
        if option_type == 'call':
            theta_part2 = -r * K * np.exp(-r * T) * stats.norm.cdf(d2)
        else:
            theta_part2 = r * K * np.exp(-r * T) * stats.norm.cdf(-d2)
            
        return (theta_part1 + theta_part2) / 365
    
    @staticmethod
    def vega(S, K, T, r, sigma):
        """Calculate option vega (volatility sensitivity)"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return S * stats.norm.pdf(d1) * np.sqrt(T) / 100

class GARCHModel:
    """GARCH model for volatility forecasting"""
    
    def __init__(self, p=1, q=1):
        self.p = p  # GARCH order
        self.q = q  # ARCH order
        self.model = None
        self.fitted_model = None
        
    def fit(self, returns):
        """Fit GARCH model to return series"""
        # Convert to percentage returns
        returns_pct = returns * 100
        
        # Fit GARCH model
        self.model = arch_model(returns_pct, vol='Garch', p=self.p, q=self.q)
        self.fitted_model = self.model.fit(disp='off')
        
        return self.fitted_model
        
    def forecast(self, horizon=1):
        """Forecast volatility"""
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")
            
        forecast = self.fitted_model.forecast(horizon=horizon)
        return forecast.variance.iloc[-1, :] / 10000  # Convert back to decimal
        
    def conditional_volatility(self):
        """Get conditional volatility"""
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before getting volatility")
            
        return self.fitted_model.conditional_volatility / 100

class KalmanFilterModel:
    """Kalman Filter for state space modeling"""
    
    def __init__(self, n_states=2):
        self.n_states = n_states
        self.kf = None
        
    def fit_pairs_trading(self, price1, price2):
        """Fit Kalman Filter for pairs trading"""
        # Prepare observations (price2 as dependent variable)
        observations = np.column_stack([price1, price2])
        
        # State transition matrix (random walk for hedge ratio)
        transition_matrix = np.eye(self.n_states)
        
        # Observation matrix [price1, 1] for linear regression
        observation_matrix = np.column_stack([price1, np.ones(len(price1))])
        
        # Initialize Kalman Filter
        self.kf = KalmanFilter(
            transition_matrices=transition_matrix,
            observation_matrices=observation_matrix,
            n_dim_state=self.n_states
        )
        
        # Fit the model
        state_means, state_covariances = self.kf.em(price2).smooth()[0:2]
        
        return state_means, state_covariances
        
    def get_hedge_ratio(self, price1, price2):
        """Get current hedge ratio for pairs trading"""
        state_means, _ = self.fit_pairs_trading(price1, price2)
        return state_means[-1, 0]  # Latest hedge ratio
        
    def get_spread(self, price1, price2):
        """Calculate spread using Kalman Filter"""
        state_means, _ = self.fit_pairs_trading(price1, price2)
        hedge_ratio = state_means[:, 0]
        intercept = state_means[:, 1]
        
        spread = price2 - hedge_ratio * price1 - intercept
        return spread

class MeanReversionModel:
    """Ornstein-Uhlenbeck process for mean reversion modeling"""
    
    def __init__(self):
        self.theta = None  # Mean reversion speed
        self.mu = None     # Long-term mean
        self.sigma = None  # Volatility
        
    def fit(self, prices):
        """Fit Ornstein-Uhlenbeck process to price series"""
        # Calculate log returns
        log_prices = np.log(prices)
        returns = np.diff(log_prices)
        
        # Estimate parameters using maximum likelihood
        def negative_log_likelihood(params):
            theta, mu, sigma = params
            if theta <= 0 or sigma <= 0:
                return np.inf
                
            dt = 1  # Daily data
            n = len(returns)
            
            # Calculate expected returns under OU process
            expected_returns = theta * (mu - log_prices[:-1]) * dt
            
            # Log likelihood
            log_likelihood = -0.5 * n * np.log(2 * np.pi * sigma**2 * dt)
            log_likelihood -= 0.5 * np.sum((returns - expected_returns)**2) / (sigma**2 * dt)
            
            return -log_likelihood
        
        # Initial parameter guess
        initial_guess = [0.1, np.mean(log_prices), np.std(returns)]
        
        # Optimize
        result = minimize(negative_log_likelihood, initial_guess, 
                         bounds=[(0.001, 10), (None, None), (0.001, 10)])
        
        if result.success:
            self.theta, self.mu, self.sigma = result.x
        else:
            # Fallback to simple estimates
            self.theta = 0.1
            self.mu = np.mean(log_prices)
            self.sigma = np.std(returns)
            
    def half_life(self):
        """Calculate half-life of mean reversion"""
        if self.theta is None:
            return None
        return np.log(2) / self.theta
        
    def expected_return(self, current_price, horizon=1):
        """Expected return given current price and time horizon"""
        if None in [self.theta, self.mu, self.sigma]:
            return 0
            
        log_current = np.log(current_price)
        expected_log_price = self.mu + (log_current - self.mu) * np.exp(-self.theta * horizon)
        expected_price = np.exp(expected_log_price)
        
        return (expected_price - current_price) / current_price

class JumpDiffusionModel:
    """Merton Jump Diffusion Model"""
    
    def __init__(self):
        self.mu = None      # Drift
        self.sigma = None   # Volatility
        self.lam = None     # Jump intensity
        self.mu_j = None    # Jump mean
        self.sigma_j = None # Jump volatility
        
    def fit(self, returns):
        """Fit jump diffusion model to returns"""
        def negative_log_likelihood(params):
            mu, sigma, lam, mu_j, sigma_j = params
            
            if sigma <= 0 or lam <= 0 or sigma_j <= 0:
                return np.inf
                
            dt = 1/252  # Daily returns
            log_likelihood = 0
            
            for r in returns:
                # Probability of no jump
                prob_no_jump = np.exp(-lam * dt) * stats.norm.pdf(r, mu * dt, sigma * np.sqrt(dt))
                
                # Probability of one jump (simplified)
                prob_jump = lam * dt * np.exp(-lam * dt) * stats.norm.pdf(r, mu * dt + mu_j, 
                                                                         np.sqrt(sigma**2 * dt + sigma_j**2))
                
                log_likelihood += np.log(prob_no_jump + prob_jump + 1e-10)
                
            return -log_likelihood
        
        # Initial parameter estimates
        mu_init = np.mean(returns) * 252
        sigma_init = np.std(returns) * np.sqrt(252)
        
        initial_guess = [mu_init, sigma_init, 0.1, 0, sigma_init * 0.5]
        bounds = [(None, None), (0.001, None), (0.001, 2), (-0.5, 0.5), (0.001, None)]
        
        try:
            result = minimize(negative_log_likelihood, initial_guess, bounds=bounds)
            if result.success:
                self.mu, self.sigma, self.lam, self.mu_j, self.sigma_j = result.x
            else:
                # Fallback to simple estimates
                self.mu = mu_init
                self.sigma = sigma_init
                self.lam = 0.1
                self.mu_j = 0
                self.sigma_j = sigma_init * 0.5
        except:
            # Fallback estimates
            self.mu = mu_init
            self.sigma = sigma_init
            self.lam = 0.1
            self.mu_j = 0
            self.sigma_j = sigma_init * 0.5
            
    def simulate_paths(self, S0, T, n_steps, n_paths=1000):
        """Simulate price paths using jump diffusion"""
        dt = T / n_steps
        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = S0
        
        for i in range(1, n_steps + 1):
            # Normal diffusion component
            dW = np.random.normal(0, np.sqrt(dt), n_paths)
            
            # Jump component
            n_jumps = np.random.poisson(self.lam * dt, n_paths)
            jump_size = np.zeros(n_paths)
            
            for j in range(n_paths):
                if n_jumps[j] > 0:
                    jump_size[j] = np.sum(np.random.normal(self.mu_j, self.sigma_j, n_jumps[j]))
            
            # Price evolution
            paths[:, i] = paths[:, i-1] * np.exp(
                (self.mu - 0.5 * self.sigma**2) * dt + 
                self.sigma * dW + 
                jump_size
            )
            
        return paths

class FractionalBrownianMotion:
    """Fractional Brownian Motion for long memory modeling"""
    
    def __init__(self, hurst=0.5):
        self.hurst = hurst
        
    def estimate_hurst(self, prices):
        """Estimate Hurst exponent using R/S analysis"""
        log_prices = np.log(prices)
        returns = np.diff(log_prices)
        
        # Calculate R/S statistic for different time scales
        time_scales = [10, 20, 50, 100, 200]
        rs_stats = []
        
        for scale in time_scales:
            if len(returns) < scale:
                continue
                
            # Divide returns into non-overlapping windows
            n_windows = len(returns) // scale
            rs_values = []
            
            for i in range(n_windows):
                window_returns = returns[i*scale:(i+1)*scale]
                
                # Calculate cumulative deviations
                mean_return = np.mean(window_returns)
                cumulative_deviations = np.cumsum(window_returns - mean_return)
                
                # Calculate range and standard deviation
                R = np.max(cumulative_deviations) - np.min(cumulative_deviations)
                S = np.std(window_returns)
                
                if S > 0:
                    rs_values.append(R / S)
            
            if rs_values:
                rs_stats.append(np.mean(rs_values))
        
        # Estimate Hurst exponent from log-log regression
        if len(rs_stats) >= 2:
            log_scales = np.log(time_scales[:len(rs_stats)])
            log_rs = np.log(rs_stats)
            
            slope, _ = np.polyfit(log_scales, log_rs, 1)
            self.hurst = slope
        
        return self.hurst
        
    def generate_fbm(self, n_points, T=1.0):
        """Generate fractional Brownian motion"""
        dt = T / n_points
        times = np.arange(0, T + dt, dt)
        
        # Covariance matrix for fBm
        def fbm_covariance(s, t, H):
            return 0.5 * (s**(2*H) + t**(2*H) - np.abs(t - s)**(2*H))
        
        # Build covariance matrix
        cov_matrix = np.zeros((len(times), len(times)))
        for i, s in enumerate(times):
            for j, t in enumerate(times):
                cov_matrix[i, j] = fbm_covariance(s, t, self.hurst)
        
        # Generate correlated Gaussian process
        try:
            fbm = np.random.multivariate_normal(np.zeros(len(times)), cov_matrix)
        except:
            # Fallback to standard Brownian motion if covariance matrix is ill-conditioned
            fbm = np.random.normal(0, np.sqrt(times))
            
        return times, fbm

class RegimeSwitchingModel:
    """Markov Regime Switching Model"""
    
    def __init__(self, n_regimes=2):
        self.n_regimes = n_regimes
        self.transition_matrix = None
        self.regime_params = None
        
    def fit(self, returns):
        """Fit regime switching model using EM algorithm (simplified)"""
        # Initialize parameters
        self.regime_params = []
        for i in range(self.n_regimes):
            self.regime_params.append({
                'mu': np.random.normal(0, 0.01),
                'sigma': np.random.uniform(0.01, 0.05)
            })
        
        # Initialize transition matrix
        self.transition_matrix = np.random.dirichlet([1] * self.n_regimes, self.n_regimes)
        
        # Simple k-means based regime identification
        from sklearn.cluster import KMeans
        
        features = np.column_stack([returns, np.abs(returns)])
        kmeans = KMeans(n_clusters=self.n_regimes, random_state=42)
        regimes = kmeans.fit_predict(features)
        
        # Update parameters based on clustering
        for regime in range(self.n_regimes):
            regime_returns = returns[regimes == regime]
            if len(regime_returns) > 0:
                self.regime_params[regime]['mu'] = np.mean(regime_returns)
                self.regime_params[regime]['sigma'] = np.std(regime_returns)
        
        # Estimate transition probabilities
        for i in range(self.n_regimes):
            for j in range(self.n_regimes):
                transitions = 0
                current_regime_count = 0
                
                for t in range(len(regimes) - 1):
                    if regimes[t] == i:
                        current_regime_count += 1
                        if regimes[t + 1] == j:
                            transitions += 1
                
                if current_regime_count > 0:
                    self.transition_matrix[i, j] = transitions / current_regime_count
        
        return regimes
        
    def predict_regime(self, recent_returns, n_recent=5):
        """Predict current regime based on recent returns"""
        if self.regime_params is None:
            return 0
            
        recent = recent_returns[-n_recent:]
        regime_probs = []
        
        for regime in range(self.n_regimes):
            mu = self.regime_params[regime]['mu']
            sigma = self.regime_params[regime]['sigma']
            
            # Calculate likelihood
            likelihood = np.prod(stats.norm.pdf(recent, mu, sigma))
            regime_probs.append(likelihood)
        
        # Return regime with highest probability
        return np.argmax(regime_probs)

# Example usage and testing
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    n_days = 1000
    
    # Simulate stock price with GARCH volatility
    returns = np.random.normal(0.001, 0.02, n_days)
    prices = 100 * np.exp(np.cumsum(returns))
    
    print("Testing Mathematical Models:")
    print("=" * 50)
    
    # Test Black-Scholes
    bs = BlackScholesModel()
    call_price = bs.call_price(S=100, K=105, T=0.25, r=0.05, sigma=0.2)
    print(f"Black-Scholes Call Price: ${call_price:.2f}")
    
    # Test GARCH
    garch = GARCHModel()
    garch.fit(returns)
    vol_forecast = garch.forecast(horizon=5)
    print(f"GARCH Volatility Forecast: {vol_forecast.iloc[0]:.4f}")
    
    # Test Mean Reversion
    mr = MeanReversionModel()
    mr.fit(prices)
    half_life = mr.half_life()
    print(f"Mean Reversion Half-Life: {half_life:.2f} days")
    
    # Test Hurst Exponent
    fbm = FractionalBrownianMotion()
    hurst = fbm.estimate_hurst(prices)
    print(f"Hurst Exponent: {hurst:.3f}")
    
    # Test Regime Switching
    rs = RegimeSwitchingModel()
    regimes = rs.fit(returns)
    current_regime = rs.predict_regime(returns)
    print(f"Current Regime: {current_regime}")
    
    print("\nAll mathematical models initialized successfully!")