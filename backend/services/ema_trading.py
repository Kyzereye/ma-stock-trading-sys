#!/usr/bin/env python3
"""
Moving Average Trading System

Supports both EMA (Exponential Moving Average) and SMA (Simple Moving Average) strategies:
- BUY signal: Price moves above 50 MA
- SELL signal: Price drops below 21 MA
- Only one trade at a time (no overlapping trades)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class MASignal:
    """Moving Average trading signal"""
    date: datetime
    signal_type: str  # 'BUY' or 'SELL'
    price: float
    ma_21: float
    ma_50: float
    reasoning: str
    confidence: float
    atr: Optional[float] = None
    trailing_stop: Optional[float] = None

@dataclass
class MATrade:
    """Moving Average trade record"""
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    entry_signal: str
    exit_signal: str
    shares: int
    pnl: Optional[float]
    pnl_percent: Optional[float]
    duration_days: Optional[int]
    exit_reason: Optional[str] = None  # 'MA_SIGNAL' or 'TRAILING_STOP'
    is_reentry: bool = False  # True if this is a re-entry trade
    reentry_count: int = 0  # Number of re-entries in this trend sequence

@dataclass
class MAResults:
    """Complete Moving Average trading results"""
    symbol: str
    start_date: datetime
    end_date: datetime
    total_days: int
    trades: List[MATrade]
    signals: List[MASignal]
    performance_metrics: Dict
    equity_curve: List[Tuple[datetime, float]]

class MATradingEngine:
    """
    Moving Average Trading Engine
    
    Implements a simple MA crossover strategy:
    - BUY when price > 50 MA
    - SELL when price < 21 MA
    - Only one trade at a time
    - Supports both EMA and SMA
    """
    
    def __init__(self, initial_capital: float = 100000, atr_period: int = 14, atr_multiplier: float = 2.0, ma_type: str = 'ema'):
        self.initial_capital = initial_capital
        self.ma_21_period = 21
        self.ma_50_period = 50
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.ma_type = ma_type.lower()  # 'ema' or 'sma'
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    def calculate_ma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Moving Average (EMA or SMA based on ma_type)"""
        if self.ma_type == 'sma':
            return self.calculate_sma(data, period)
        else:  # default to ema
            return self.calculate_ema(data, period)
    
    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range (ATR)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR as EMA of True Range
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def run_analysis(self, df: pd.DataFrame, symbol: str) -> MAResults:
        """
        Run Moving Average trading analysis
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            
        Returns:
            MAResults object with complete analysis
        """
        logger.info(f"Starting {self.ma_type.upper()} analysis for {symbol}")
        
        if len(df) < self.ma_50_period:
            raise ValueError(f"Not enough data for {self.ma_type.upper()} analysis. Need at least {self.ma_50_period} days")
        
        # Calculate Moving Averages and ATR
        df['ma_21'] = self.calculate_ma(df['close'], self.ma_21_period)
        df['ma_50'] = self.calculate_ma(df['close'], self.ma_50_period)
        df['atr'] = self.calculate_atr(df, self.atr_period)
        
        # Generate signals
        signals = self._generate_signals(df)
        
        # Execute trades
        trades = self._execute_trades(df, signals)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(trades)
        
        # Generate equity curve
        equity_curve = self._generate_equity_curve(df, trades)
        
        return MAResults(
            symbol=symbol,
            start_date=df.index[0],
            end_date=df.index[-1],
            total_days=len(df),
            trades=trades,
            signals=signals,
            performance_metrics=performance_metrics,
            equity_curve=equity_curve
        )
    
    def _generate_signals(self, df: pd.DataFrame) -> List[MASignal]:
        """Generate Enhanced Moving Average trading signals with re-entry logic"""
        signals = []
        in_trade = False
        current_trailing_stop = None
        highest_price_since_entry = None
        last_exit_date = None
        reentry_count = 0
        trend_start_date = None
        
        # Start from max(ma_50_period, atr_period) to ensure both are calculated
        start_index = max(self.ma_50_period, self.atr_period)
        
        for i in range(start_index, len(df)):
            current_price = df.iloc[i]['close']
            ma_21 = df.iloc[i]['ma_21']
            ma_50 = df.iloc[i]['ma_50']
            atr = df.iloc[i]['atr']
            date = df.index[i]
            
            # Skip if indicators are not calculated yet
            if pd.isna(ma_21) or pd.isna(ma_50) or pd.isna(atr):
                continue
            
            # Check if we're in a new trend (price above 50 MA after being below)
            is_new_trend = (not in_trade and 
                           current_price > ma_50 and 
                           i > 0 and 
                           df.iloc[i-1]['close'] <= df.iloc[i-1]['ma_50'])
            
            # Check if we can re-enter (price above 21 MA after exit, with trend confirmation)
            can_reenter = (not in_trade and 
                          last_exit_date is not None and
                          current_price > ma_21 and 
                          ma_21 > ma_50 and  # Trend confirmation: 21 MA above 50 MA
                          i > 0 and 
                          df.iloc[i-1]['close'] <= df.iloc[i-1]['ma_21'])
            
            # ENTRY LOGIC
            if is_new_trend:
                # Primary entry: Price closes above 50 MA
                confidence = min(0.9, abs(current_price - ma_50) / ma_50 * 10)
                current_trailing_stop = current_price - (atr * self.atr_multiplier)
                highest_price_since_entry = current_price
                trend_start_date = date
                reentry_count = 0
                
                signals.append(MASignal(
                    date=date,
                    signal_type='BUY',
                    price=current_price,
                    ma_21=ma_21,
                    ma_50=ma_50,
                    reasoning=f"Primary entry: Price {current_price:.2f} closed above 50 {self.ma_type.upper()} {ma_50:.2f}",
                    confidence=confidence,
                    atr=atr,
                    trailing_stop=current_trailing_stop
                ))
                in_trade = True
                
            elif can_reenter:
                # Re-entry: Price closes above 21 MA after exit
                confidence = min(0.8, abs(current_price - ma_21) / ma_21 * 10)  # Slightly lower confidence
                current_trailing_stop = current_price - (atr * self.atr_multiplier)
                highest_price_since_entry = current_price
                reentry_count += 1
                
                signals.append(MASignal(
                    date=date,
                    signal_type='BUY',
                    price=current_price,
                    ma_21=ma_21,
                    ma_50=ma_50,
                    reasoning=f"Re-entry #{reentry_count}: Price {current_price:.2f} closed above 21 {self.ma_type.upper()} {ma_21:.2f} (trend confirmed: 21 MA > 50 MA)",
                    confidence=confidence,
                    atr=atr,
                    trailing_stop=current_trailing_stop
                ))
                in_trade = True
            
            # EXIT LOGIC (only if in trade)
            elif in_trade:
                # Update highest price since entry
                if highest_price_since_entry is None or current_price > highest_price_since_entry:
                    highest_price_since_entry = current_price
                    # Update trailing stop: highest price - (ATR * multiplier)
                    current_trailing_stop = highest_price_since_entry - (atr * self.atr_multiplier)
                
                # Check for SELL signals
                sell_triggered = False
                sell_reason = ""
                
                if current_price < ma_21:
                    # Check if this is a new signal (price closed above 21 MA in previous period)
                    if i > 0 and df.iloc[i-1]['close'] >= df.iloc[i-1]['ma_21']:
                        sell_triggered = True
                        sell_reason = f"Price {current_price:.2f} closed below 21 {self.ma_type.upper()} {ma_21:.2f}"
                
                elif current_trailing_stop is not None and current_price < current_trailing_stop:
                    sell_triggered = True
                    sell_reason = f"Price {current_price:.2f} hit trailing stop {current_trailing_stop:.2f}"
                
                elif current_price < ma_50:
                    # Major trend break: Price below 50 MA
                    sell_triggered = True
                    sell_reason = f"Major trend break: Price {current_price:.2f} closed below 50 {self.ma_type.upper()} {ma_50:.2f}"
                
                if sell_triggered:
                    confidence = min(0.9, abs(current_price - ma_21) / ma_21 * 10)
                    signals.append(MASignal(
                        date=date,
                        signal_type='SELL',
                        price=current_price,
                        ma_21=ma_21,
                        ma_50=ma_50,
                        reasoning=sell_reason,
                        confidence=confidence,
                        atr=atr,
                        trailing_stop=current_trailing_stop
                    ))
                    in_trade = False
                    last_exit_date = date
                    current_trailing_stop = None
                    highest_price_since_entry = None
        
        return signals
    
    def _execute_trades(self, df: pd.DataFrame, signals: List[MASignal]) -> List[MATrade]:
        """Execute trades based on signals using next day's open prices with re-entry logic"""
        trades = []
        current_position = None
        available_capital = self.initial_capital
        reentry_count = 0
        
        # Create a mapping of dates to DataFrame indices for quick lookup
        date_to_index = {df.index[i]: i for i in range(len(df))}
        
        for signal in signals:
            if signal.signal_type == 'BUY' and current_position is None:
                # Find the next day's open price for entry
                signal_index = date_to_index.get(signal.date)
                if signal_index is not None and signal_index + 1 < len(df):
                    next_day_open = df.iloc[signal_index + 1]['open']
                    
                    # Determine if this is a re-entry and adjust position size
                    is_reentry = 'Re-entry' in signal.reasoning
                    if is_reentry:
                        reentry_count += 1
                        # Use 50% of available capital for re-entries
                        position_capital = available_capital * 0.5
                    else:
                        reentry_count = 0
                        # Use full available capital for primary entries
                        position_capital = available_capital
                    
                    shares = int(position_capital / next_day_open)
                    if shares > 0:
                        current_position = {
                            'entry_date': signal.date,
                            'entry_price': next_day_open,
                            'entry_signal': signal.reasoning,
                            'shares': shares,
                            'is_reentry': is_reentry,
                            'reentry_count': reentry_count
                        }
                        available_capital -= shares * next_day_open
                        
                        entry_type = "Re-entry" if is_reentry else "Primary entry"
                        logger.info(f"Opened {entry_type} BUY position: {shares} shares at ${next_day_open:.2f} (next day open)")
            
            elif signal.signal_type == 'SELL' and current_position is not None:
                # Find the next day's open price for exit
                signal_index = date_to_index.get(signal.date)
                if signal_index is not None and signal_index + 1 < len(df):
                    next_day_open = df.iloc[signal_index + 1]['open']
                    shares = current_position['shares']
                    pnl = shares * (next_day_open - current_position['entry_price'])
                    pnl_percent = (next_day_open - current_position['entry_price']) / current_position['entry_price'] * 100
                    duration = (signal.date - current_position['entry_date']).days
                    
                    # Determine exit reason
                    if 'trailing stop' in signal.reasoning.lower():
                        exit_reason = 'TRAILING_STOP'
                    elif 'Major trend break' in signal.reasoning:
                        exit_reason = 'TREND_BREAK'
                    else:
                        exit_reason = 'MA_SIGNAL'
                    
                    trade = MATrade(
                        entry_date=current_position['entry_date'],
                        exit_date=signal.date,
                        entry_price=current_position['entry_price'],
                        exit_price=next_day_open,
                        entry_signal=current_position['entry_signal'],
                        exit_signal=signal.reasoning,
                        shares=shares,
                        pnl=pnl,
                        pnl_percent=pnl_percent,
                        duration_days=duration,
                        exit_reason=exit_reason,
                        is_reentry=current_position['is_reentry'],
                        reentry_count=current_position['reentry_count']
                    )
                    
                    trades.append(trade)
                    available_capital += shares * next_day_open
                    
                    exit_type = "Re-entry" if current_position['is_reentry'] else "Primary"
                    logger.info(f"Closed {exit_type} position: PnL ${pnl:.2f} ({pnl_percent:.2f}%) over {duration} days")
                    current_position = None
        
        # Close any remaining position at the end
        if current_position is not None:
            final_price = df.iloc[-1]['close']
            final_date = df.index[-1]
            shares = current_position['shares']
            pnl = shares * (final_price - current_position['entry_price'])
            pnl_percent = (final_price - current_position['entry_price']) / current_position['entry_price'] * 100
            duration = (final_date - current_position['entry_date']).days
            
            trade = MATrade(
                entry_date=current_position['entry_date'],
                exit_date=final_date,
                entry_price=current_position['entry_price'],
                exit_price=final_price,
                entry_signal=current_position['entry_signal'],
                exit_signal="End of period - position closed",
                shares=shares,
                pnl=pnl,
                pnl_percent=pnl_percent,
                duration_days=duration
            )
            
            trades.append(trade)
            logger.info(f"Closed final position: PnL ${pnl:.2f} ({pnl_percent:.2f}%) over {duration} days")
        
        return trades
    
    def _calculate_performance_metrics(self, trades: List[MATrade]) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_return_percent': 0.0,
                'avg_trade_duration': 0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t.pnl for t in trades if t.pnl is not None)
        total_return_percent = (total_pnl / self.initial_capital) * 100
        
        avg_duration = sum(t.duration_days for t in trades if t.duration_days is not None) / total_trades
        
        # Calculate max drawdown
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in trades:
            if trade.pnl is not None:
                cumulative_pnl += trade.pnl
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                drawdown = peak - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return_percent': total_return_percent,
            'avg_trade_duration': avg_duration,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': 0.0  # Simplified for now
        }
    
    def _generate_equity_curve(self, df: pd.DataFrame, trades: List[MATrade]) -> List[Tuple[datetime, float]]:
        """Generate equity curve"""
        equity_curve = []
        current_equity = self.initial_capital
        
        # Create a mapping of dates to trade PnL
        trade_pnl_by_date = {}
        for trade in trades:
            if trade.exit_date and trade.pnl is not None:
                trade_pnl_by_date[trade.exit_date] = trade.pnl
        
        for date in df.index:
            if date in trade_pnl_by_date:
                current_equity += trade_pnl_by_date[date]
            equity_curve.append((date, current_equity))
        
        return equity_curve
