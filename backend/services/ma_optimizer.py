"""
Moving Average Pair Optimization Service

This service finds optimal MA pairs for different stocks and market conditions.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from itertools import product

from .ema_trading import MATradingEngine
from utils.data_retrieval import get_stock_data

logger = logging.getLogger(__name__)

@dataclass
class MAOptimizationResult:
    """Result of MA pair optimization"""
    fast_ma: int
    slow_ma: int
    ma_distance: int
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float
    symbol: str
    date_range: str

@dataclass
class OptimizationSummary:
    """Summary of optimization results"""
    symbol: str
    best_pair: Optional[MAOptimizationResult]
    top_5_pairs: List[MAOptimizationResult]
    all_results: List[MAOptimizationResult]
    optimization_date: datetime
    parameters_used: Dict

class MAOptimizer:
    """Moving Average pair optimizer"""
    
    def __init__(self, initial_capital: float = 100000, 
                 atr_period: int = 14, 
                 atr_multiplier: float = 2.0,
                 ma_type: str = 'ema'):
        self.initial_capital = initial_capital
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.ma_type = ma_type
    
    def optimize_ma_pairs(self, symbol: str, days: int = 365,
                         fast_ma_range: Tuple[int, int] = (5, 30),
                         slow_ma_range: Tuple[int, int] = (20, 100),
                         min_distance: int = 10) -> OptimizationSummary:
        """
        Optimize MA pairs for a given symbol
        
        Args:
            symbol: Stock symbol to optimize
            days: Number of days to analyze
            fast_ma_range: Range for fast MA (min, max)
            slow_ma_range: Range for slow MA (min, max)
            min_distance: Minimum distance between fast and slow MA
        """
        logger.info(f"Starting MA optimization for {symbol}")
        
        # Get stock data using shared method
        df = get_stock_data(symbol, days)
        if df is None or len(df) < 100:
            raise ValueError(f"Insufficient data for {symbol}")
        
        # Generate all valid MA pairs
        ma_pairs = self._generate_ma_pairs(fast_ma_range, slow_ma_range, min_distance)
        logger.info(f"Testing {len(ma_pairs)} MA pairs for {symbol}")
        
        # Test each pair
        results = []
        for fast_ma, slow_ma in ma_pairs:
            try:
                result = self._test_ma_pair(df, symbol, fast_ma, slow_ma)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to test pair ({fast_ma}, {slow_ma}): {e}")
                continue
        
        # Filter out None results and sort by total return
        results = [r for r in results if r is not None]
        results.sort(key=lambda x: x.total_return_percent, reverse=True)
        
        # Create summary
        summary = OptimizationSummary(
            symbol=symbol,
            best_pair=results[0] if results else None,
            top_5_pairs=results[:5],
            all_results=results,
            optimization_date=datetime.now(),
            parameters_used={
                'fast_ma_range': fast_ma_range,
                'slow_ma_range': slow_ma_range,
                'min_distance': min_distance,
                'days': days,
                'atr_period': self.atr_period,
                'atr_multiplier': self.atr_multiplier,
                'ma_type': self.ma_type
            }
        )
        
        logger.info(f"Optimization complete for {symbol}. Best pair: {summary.best_pair.fast_ma},{summary.best_pair.slow_ma}")
        return summary
    
    def compare_ma_pairs(self, symbol: str, ma_pairs: List[Tuple[int, int]], 
                        days: int = 365) -> List[MAOptimizationResult]:
        """
        Compare specific MA pairs for a symbol
        
        Args:
            symbol: Stock symbol
            ma_pairs: List of (fast_ma, slow_ma) tuples to compare
            days: Number of days to analyze
        """
        logger.info(f"Comparing {len(ma_pairs)} MA pairs for {symbol}")
        
        df = get_stock_data(symbol, days)
        if df is None:
            raise ValueError(f"No data available for {symbol}")
        
        results = []
        for fast_ma, slow_ma in ma_pairs:
            try:
                result = self._test_ma_pair(df, symbol, fast_ma, slow_ma)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to test pair ({fast_ma}, {slow_ma}): {e}")
                continue
        
        return sorted(results, key=lambda x: x.total_return_percent, reverse=True)
    
    def universal_optimization(self, symbols: List[str], days: int = 365,
                              fast_ma_range: Tuple[int, int] = (5, 30),
                              slow_ma_range: Tuple[int, int] = (20, 100),
                              min_distance: int = 10) -> Dict[str, OptimizationSummary]:
        """
        Run optimization across multiple symbols to find universal patterns
        """
        logger.info(f"Running universal optimization for {len(symbols)} symbols")
        
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.optimize_ma_pairs(
                    symbol, days, fast_ma_range, slow_ma_range, min_distance
                )
            except Exception as e:
                logger.error(f"Failed to optimize {symbol}: {e}")
                continue
        
        return results
    
    
    def _generate_ma_pairs(self, fast_range: Tuple[int, int], 
                          slow_range: Tuple[int, int], 
                          min_distance: int) -> List[Tuple[int, int]]:
        """Generate all valid MA pairs within the specified ranges"""
        pairs = []
        
        for fast_ma in range(fast_range[0], fast_range[1] + 1):
            for slow_ma in range(slow_range[0], slow_range[1] + 1):
                if slow_ma - fast_ma >= min_distance:
                    pairs.append((fast_ma, slow_ma))
        
        return pairs
    
    def _test_ma_pair(self, df: pd.DataFrame, symbol: str, 
                     fast_ma: int, slow_ma: int) -> Optional[MAOptimizationResult]:
        """Test a specific MA pair and return performance metrics"""
        try:
            # Create trading engine with custom MA periods
            engine = MATradingEngine(
                initial_capital=self.initial_capital,
                atr_period=self.atr_period,
                atr_multiplier=self.atr_multiplier,
                ma_type=self.ma_type,
                custom_fast_ma=fast_ma,
                custom_slow_ma=slow_ma
            )
            
            # Run analysis
            results = engine.run_analysis(df, symbol)
            
            if not results:
                logger.warning(f"Analysis returned None for {symbol} with MA pair ({fast_ma}, {slow_ma})")
                return None
                
            if not results.trades:
                logger.warning(f"No trades generated for {symbol} with MA pair ({fast_ma}, {slow_ma})")
                return None
                
            if not results.performance_metrics:
                logger.warning(f"No performance metrics for {symbol} with MA pair ({fast_ma}, {slow_ma})")
                return None
            
            # Calculate additional metrics
            sharpe_ratio = self._calculate_sharpe_ratio(results.trades)
            max_drawdown = self._calculate_max_drawdown(results.equity_curve)
            profit_factor = self._calculate_profit_factor(results.trades)
            avg_duration = np.mean([t.duration_days for t in results.trades if t.duration_days])
            
            return MAOptimizationResult(
                fast_ma=fast_ma,
                slow_ma=slow_ma,
                ma_distance=slow_ma - fast_ma,
                total_return_percent=results.performance_metrics['total_return_percent'],
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=results.performance_metrics['win_rate'],
                profit_factor=profit_factor,
                total_trades=results.performance_metrics['total_trades'],
                avg_trade_duration=avg_duration,
                symbol=symbol,
                date_range=f"{df.index[0].date()} to {df.index[-1].date()}"
            )
            
        except Exception as e:
            logger.warning(f"Error testing pair ({fast_ma}, {slow_ma}): {e}")
            return None
    
    def _calculate_sharpe_ratio(self, trades: List) -> float:
        """Calculate Sharpe ratio from trade returns"""
        if not trades or len(trades) < 2:
            return 0.0
        
        returns = [t.pnl_percent for t in trades if t.pnl_percent is not None]
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Assuming risk-free rate of 2% annually
        risk_free_rate = 2.0 / 252  # Daily risk-free rate
        return (mean_return - risk_free_rate) / std_return
    
    def _calculate_max_drawdown(self, equity_curve: List[Tuple[datetime, float]]) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        equity_values = [point[1] for point in equity_curve]
        peak = equity_values[0]
        max_dd = 0.0
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100  # Return as percentage
    
    def _calculate_profit_factor(self, trades: List) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        if not trades:
            return 0.0
        
        gross_profit = sum(t.pnl for t in trades if t.pnl and t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl and t.pnl < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
