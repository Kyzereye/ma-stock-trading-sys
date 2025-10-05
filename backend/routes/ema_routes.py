#!/usr/bin/env python3
"""
EMA Trading API Routes

Provides endpoints for EMA trading analysis and backtesting
"""

from flask import Blueprint, request, jsonify
from services.ema_trading import MATradingEngine
from utils.database import get_db_connection
import pandas as pd
import logging

logger = logging.getLogger(__name__)

ema_bp = Blueprint('ema', __name__, url_prefix='/api/ema')


@ema_bp.route('/analyze', methods=['POST'])
def analyze_ema_trading_post():
    """Analyze EMA trading for a specific symbol via POST request"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        initial_capital = float(data.get('initial_capital', 100000))
        days = int(data.get('days', 0))  # 0 means all data
        atr_period = int(data.get('atr_period', 14))
        atr_multiplier = float(data.get('atr_multiplier', 2.0))
        
        # Get data from database
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        
        if days > 0:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC 
            LIMIT %s
            """
            cursor.execute(query, (symbol, days))
        else:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC
            """
            cursor.execute(query, (symbol,))
        
        data = cursor.fetchall()
        cursor.close()
        conn.connection.close()
        
        if not data:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Run EMA analysis
        engine = EMATradingEngine(initial_capital, atr_period, atr_multiplier)
        results = engine.run_analysis(df, symbol)
        
        # Convert results to JSON-serializable format
        response = {
            'symbol': results.symbol,
            'start_date': results.start_date.isoformat(),
            'end_date': results.end_date.isoformat(),
            'total_days': results.total_days,
            'performance_metrics': results.performance_metrics,
            'trades': [
                {
                    'entry_date': trade.entry_date.isoformat(),
                    'exit_date': trade.exit_date.isoformat() if trade.exit_date else None,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'entry_signal': trade.entry_signal,
                    'exit_signal': trade.exit_signal,
                    'shares': trade.shares,
                    'pnl': trade.pnl,
                    'pnl_percent': trade.pnl_percent,
                    'duration_days': trade.duration_days,
                    'exit_reason': trade.exit_reason,
                    'is_reentry': trade.is_reentry,
                    'reentry_count': trade.reentry_count
                }
                for trade in results.trades
            ],
            'signals': [
                {
                    'date': signal.date.isoformat(),
                    'signal_type': signal.signal_type,
                    'price': signal.price,
                    'ma_21': signal.ma_21,
                    'ma_50': signal.ma_50,
                    'reasoning': signal.reasoning,
                    'confidence': signal.confidence,
                    'atr': signal.atr,
                    'trailing_stop': signal.trailing_stop
                }
                for signal in results.signals
            ],
            'equity_curve': [
                {'date': date.isoformat(), 'equity': equity}
                for date, equity in results.equity_curve
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error analyzing EMA trading: {e}")
        return jsonify({'error': str(e)}), 500

@ema_bp.route('/analyze/<symbol>', methods=['GET'])
def analyze_ema_trading(symbol):
    """Analyze EMA trading for a specific symbol"""
    try:
        # Get parameters
        initial_capital = float(request.args.get('initial_capital', 100000))
        days = int(request.args.get('days', 365))
        atr_period = int(request.args.get('atr_period', 14))
        atr_multiplier = float(request.args.get('atr_multiplier', 2.0))
        ma_type = request.args.get('ma_type', 'ema').lower()  # 'ema' or 'sma'
        
        # Get data from database
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        
        if days > 0:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC 
            LIMIT %s
            """
            cursor.execute(query, (symbol.upper(), days))
        else:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC
            """
            cursor.execute(query, (symbol.upper(),))
        data = cursor.fetchall()
        cursor.close()
        conn.connection.close()
        
        if not data:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Run Moving Average analysis
        engine = MATradingEngine(initial_capital, atr_period, atr_multiplier, ma_type)
        results = engine.run_analysis(df, symbol.upper())
        
        # Convert results to JSON-serializable format
        response = {
            'symbol': results.symbol,
            'start_date': results.start_date.isoformat(),
            'end_date': results.end_date.isoformat(),
            'total_days': results.total_days,
            'performance_metrics': results.performance_metrics,
            'trades': [
                {
                    'entry_date': trade.entry_date.isoformat(),
                    'exit_date': trade.exit_date.isoformat() if trade.exit_date else None,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'entry_signal': trade.entry_signal,
                    'exit_signal': trade.exit_signal,
                    'shares': trade.shares,
                    'pnl': trade.pnl,
                    'pnl_percent': trade.pnl_percent,
                    'duration_days': trade.duration_days,
                    'exit_reason': trade.exit_reason,
                    'is_reentry': trade.is_reentry,
                    'reentry_count': trade.reentry_count
                }
                for trade in results.trades
            ],
            'signals': [
                {
                    'date': signal.date.isoformat(),
                    'signal_type': signal.signal_type,
                    'price': signal.price,
                    'ma_21': signal.ma_21,
                    'ma_50': signal.ma_50,
                    'reasoning': signal.reasoning,
                    'confidence': signal.confidence,
                    'atr': signal.atr,
                    'trailing_stop': signal.trailing_stop
                }
                for signal in results.signals
            ],
            'equity_curve': [
                {'date': date.isoformat(), 'equity': equity}
                for date, equity in results.equity_curve
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error analyzing EMA trading for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@ema_bp.route('/signals/<symbol>', methods=['GET'])
def get_ema_signals(symbol):
    """Get EMA trading signals for a specific symbol"""
    try:
        days = int(request.args.get('days', 100))
        
        # Get data from database
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        
        if days > 0:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC 
            LIMIT %s
            """
            cursor.execute(query, (symbol.upper(), days))
        else:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC
            """
            cursor.execute(query, (symbol.upper(),))
        data = cursor.fetchall()
        cursor.close()
        conn.connection.close()
        
        if not data:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Run EMA analysis
        engine = EMATradingEngine(100000, 14, 2.0)
        results = engine.run_analysis(df, symbol.upper())
        
        # Return only signals
        response = {
            'symbol': results.symbol,
            'signals': [
                {
                    'date': signal.date.isoformat(),
                    'signal_type': signal.signal_type,
                    'price': signal.price,
                    'ma_21': signal.ma_21,
                    'ma_50': signal.ma_50,
                    'reasoning': signal.reasoning,
                    'confidence': signal.confidence,
                    'atr': signal.atr,
                    'trailing_stop': signal.trailing_stop
                }
                for signal in results.signals
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting EMA signals for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@ema_bp.route('/summary/<symbol>', methods=['GET'])
def get_ema_summary(symbol):
    """Get EMA trading summary for a specific symbol"""
    try:
        initial_capital = float(request.args.get('initial_capital', 100000))
        days = int(request.args.get('days', 365))
        
        # Get data from database
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        
        if days > 0:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC 
            LIMIT %s
            """
            cursor.execute(query, (symbol.upper(), days))
        else:
            query = """
            SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
            FROM daily_stock_data d
            JOIN stock_symbols s ON d.symbol_id = s.id
            WHERE s.symbol = %s 
            ORDER BY d.date DESC
            """
            cursor.execute(query, (symbol.upper(),))
        data = cursor.fetchall()
        cursor.close()
        conn.connection.close()
        
        if not data:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Run EMA analysis
        engine = EMATradingEngine(initial_capital, 14, 2.0)
        results = engine.run_analysis(df, symbol.upper())
        
        # Return summary
        response = {
            'symbol': results.symbol,
            'period': f"{results.start_date.strftime('%Y-%m-%d')} to {results.end_date.strftime('%Y-%m-%d')}",
            'total_days': results.total_days,
            'performance_metrics': results.performance_metrics,
            'recent_signals': [
                {
                    'date': signal.date.isoformat(),
                    'signal_type': signal.signal_type,
                    'price': signal.price,
                    'reasoning': signal.reasoning
                }
                for signal in results.signals[-5:]  # Last 5 signals
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting EMA summary for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500
