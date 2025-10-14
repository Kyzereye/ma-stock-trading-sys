#!/usr/bin/env python3
"""
Performance Analyzer Utility

Pre-computes stock performance metrics and stores them in the database.
This is used by data update scripts to maintain up-to-date performance metrics.
"""

import pandas as pd
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import logging

from utils.database import get_db_connection
from services.ema_trading import MATradingEngine

logger = logging.getLogger(__name__)

def analyze_and_store_performance(
    symbol: str, 
    df: pd.DataFrame, 
    analysis_params: Dict[str, Any],
    analysis_date: Optional[date] = None
) -> bool:
    """
    Analyze stock performance and store results in database
    
    Args:
        symbol: Stock symbol
        df: Stock data DataFrame
        analysis_params: Analysis parameters (capital, ATR settings, etc.)
        analysis_date: Date for analysis (defaults to today)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if analysis_date is None:
            analysis_date = date.today()
        
        # Check if we have enough data
        if df is None or len(df) < 30:
            logger.warning(f"Insufficient data for {symbol}: {len(df) if df is not None else 0} days")
            return False
        
        # Extract analysis parameters
        initial_capital = analysis_params.get('initial_capital', 100000)
        atr_period = analysis_params.get('atr_period', 14)
        atr_multiplier = analysis_params.get('atr_multiplier', 2.0)
        ma_type = analysis_params.get('ma_type', 'ema')
        position_sizing_percentage = analysis_params.get('position_sizing_percentage', 5.0)
        days = analysis_params.get('days', 365)
        
        # Run analysis
        engine = MATradingEngine(
            initial_capital=initial_capital,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            ma_type=ma_type,
            custom_fast_ma=None,
            custom_slow_ma=None,
            mean_reversion_threshold=10.0,
            position_sizing_percentage=position_sizing_percentage
        )
        
        results = engine.run_analysis(df, symbol)
        
        # Calculate metrics
        total_trades = len(results.trades)
        winning_trades = len([t for t in results.trades if t.pnl and t.pnl > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Handle performance metrics format
        if isinstance(results.performance_metrics, dict):
            total_pnl = results.performance_metrics['total_pnl']
            sharpe_ratio = results.performance_metrics['sharpe_ratio']
        else:
            total_pnl = results.performance_metrics.total_pnl
            sharpe_ratio = results.performance_metrics.sharpe_ratio
        
        total_return_pct = (total_pnl / initial_capital) * 100
        
        # Store in database
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        
        # Get symbol_id
        cursor.execute("SELECT id FROM stock_symbols WHERE symbol = %s", (symbol,))
        symbol_result = cursor.fetchone()
        if not symbol_result:
            logger.error(f"Symbol {symbol} not found in stock_symbols table")
            cursor.close()
            conn.connection.close()
            return False
        
        symbol_id = symbol_result[0] if isinstance(symbol_result, tuple) else symbol_result['id']
        
        # Store or update performance metrics
        cursor.execute("""
            INSERT INTO stock_performance_metrics 
            (symbol_id, analysis_date, total_return_pct, total_pnl, win_rate, total_trades, sharpe_ratio, analysis_params)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            total_return_pct = VALUES(total_return_pct),
            total_pnl = VALUES(total_pnl),
            win_rate = VALUES(win_rate),
            total_trades = VALUES(total_trades),
            sharpe_ratio = VALUES(sharpe_ratio),
            analysis_params = VALUES(analysis_params),
            updated_at = CURRENT_TIMESTAMP
        """, (
            symbol_id,
            analysis_date,
            round(total_return_pct, 2),
            round(total_pnl, 2),
            round(win_rate, 1),
            total_trades,
            round(sharpe_ratio, 2),
            json.dumps(analysis_params)
        ))
        
        cursor.close()
        conn.connection.close()
        
        logger.info(f"Stored performance metrics for {symbol}: {total_return_pct:.2f}% return, {total_trades} trades")
        return True
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return False

def get_top_performers_from_db(
    limit: int = 10,
    analysis_date: Optional[date] = None,
    analysis_params: Optional[Dict[str, Any]] = None
) -> list:
    """
    Get top performing stocks from pre-computed database results
    
    Args:
        limit: Number of top performers to return
        analysis_date: Analysis date to filter by (defaults to latest)
        analysis_params: Analysis parameters to match (optional)
    
    Returns:
        list: Top performing stocks with metrics
    """
    try:
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        
        # Build query
        if analysis_date:
            date_filter = "AND p.analysis_date = %s"
            params = [analysis_date]
        else:
            date_filter = "AND p.analysis_date = (SELECT MAX(analysis_date) FROM stock_performance_metrics)"
            params = []
        
        # Add analysis parameters filter if provided (flexible matching)
        params_filter = ""
        if analysis_params:
            # For now, just get the latest analysis for each symbol
            # In the future, we could add more sophisticated parameter matching
            params_filter = ""
        
        query = f"""
            SELECT 
                s.symbol,
                s.company_name,
                p.total_return_pct,
                p.total_pnl,
                p.win_rate,
                p.total_trades,
                p.sharpe_ratio,
                p.analysis_date
            FROM stock_performance_metrics p
            JOIN stock_symbols s ON p.symbol_id = s.id
            WHERE 1=1 {date_filter} {params_filter}
            ORDER BY p.total_return_pct DESC
            LIMIT %s
        """
        
        params.append(limit)
        cursor.execute(query, params)
        
        results = cursor.fetchall()
        cursor.close()
        conn.connection.close()
        
        # Convert to list of dictionaries
        top_performers = []
        for row in results:
            if isinstance(row, dict):
                top_performers.append({
                    'symbol': row['symbol'],
                    'company_name': row['company_name'],
                    'total_return_pct': row['total_return_pct'],
                    'total_pnl': row['total_pnl'],
                    'win_rate': row['win_rate'],
                    'total_trades': row['total_trades'],
                    'sharpe_ratio': row['sharpe_ratio']
                })
            else:
                top_performers.append({
                    'symbol': row[0],
                    'company_name': row[1],
                    'total_return_pct': row[2],
                    'total_pnl': row[3],
                    'win_rate': row[4],
                    'total_trades': row[5],
                    'sharpe_ratio': row[6]
                })
        
        return top_performers
        
    except Exception as e:
        logger.error(f"Error getting top performers from database: {e}")
        return []

def get_analysis_stats() -> Dict[str, Any]:
    """
    Get statistics about stored performance analyses
    
    Returns:
        dict: Analysis statistics
    """
    try:
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        
        # Get total analyses
        cursor.execute("SELECT COUNT(*) FROM stock_performance_metrics")
        result = cursor.fetchone()
        total_analyses = result[0] if isinstance(result, tuple) else result['COUNT(*)']
        
        # Get latest analysis date
        cursor.execute("SELECT MAX(analysis_date) FROM stock_performance_metrics")
        result = cursor.fetchone()
        latest_date = result[0] if isinstance(result, tuple) else result['MAX(analysis_date)']
        
        # Get unique symbols analyzed
        cursor.execute("SELECT COUNT(DISTINCT symbol_id) FROM stock_performance_metrics")
        result = cursor.fetchone()
        unique_symbols = result[0] if isinstance(result, tuple) else result['COUNT(DISTINCT symbol_id)']
        
        cursor.close()
        conn.connection.close()
        
        return {
            'total_analyses': total_analyses,
            'unique_symbols': unique_symbols,
            'latest_analysis_date': latest_date
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis stats: {e}")
        return {}
