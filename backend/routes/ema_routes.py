#!/usr/bin/env python3
"""
EMA Trading API Routes

Provides endpoints for EMA trading analysis and backtesting
"""

from flask import Blueprint, request, jsonify
from services.ema_trading import MATradingEngine
from utils.data_retrieval import get_stock_data
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
        mean_reversion_threshold = float(data.get('mean_reversion_threshold', 10.0))
        position_sizing_percentage = float(data.get('position_sizing_percentage', 5.0))
        
        # Get data from database using shared method
        df = get_stock_data(symbol, days)
        if df is None:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Run EMA analysis
        engine = MATradingEngine(initial_capital, atr_period, atr_multiplier, 'ema', None, None, mean_reversion_threshold, position_sizing_percentage)
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
            'mean_reversion_alerts': [
                {
                    'date': alert.date.isoformat(),
                    'price': alert.price,
                    'ma_21': alert.ma_21,
                    'distance_percent': alert.distance_percent,
                    'reasoning': alert.reasoning
                }
                for alert in results.mean_reversion_alerts
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
        
        # Get data from database using shared method
        df = get_stock_data(symbol, days)
        if df is None:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
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
        
        # Get data from database using shared method
        df = get_stock_data(symbol, days)
        if df is None:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Run EMA analysis
        engine = MATradingEngine(100000, 14, 2.0, 'ema', None, None, 7.0)
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
            ],
            'mean_reversion_alerts': [
                {
                    'date': alert.date.isoformat(),
                    'price': alert.price,
                    'ma_21': alert.ma_21,
                    'distance_percent': alert.distance_percent,
                    'reasoning': alert.reasoning
                }
                for alert in results.mean_reversion_alerts
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
        
        # Get data from database using shared method
        df = get_stock_data(symbol, days)
        if df is None:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Run EMA analysis
        engine = MATradingEngine(initial_capital, 14, 2.0, 'ema', None, None, 7.0)
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
            ],
            'recent_mean_reversion_alerts': [
                {
                    'date': alert.date.isoformat(),
                    'price': alert.price,
                    'distance_percent': alert.distance_percent,
                    'reasoning': alert.reasoning
                }
                for alert in results.mean_reversion_alerts[-5:]  # Last 5 alerts
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting EMA summary for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@ema_bp.route('/top-performers', methods=['POST'])
def get_top_performers():
    """Analyze all stocks and return top 5 performers"""
    try:
        logger.info("Starting top performers analysis")
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        initial_capital = float(data.get('initial_capital', 100000))
        days = int(data.get('days', 365))  # Default to 1 year
        atr_period = int(data.get('atr_period', 14))
        atr_multiplier = float(data.get('atr_multiplier', 2.0))
        ma_type = data.get('ma_type', 'ema')
        position_sizing_percentage = float(data.get('position_sizing_percentage', 5.0))
        
        logger.info(f"Parameters: capital={initial_capital}, days={days}, atr_period={atr_period}, atr_multiplier={atr_multiplier}, ma_type={ma_type}, position_sizing={position_sizing_percentage}")
        
        # Import required modules
        logger.info("Importing required modules")
        from utils.database import get_db_connection
        from utils.data_retrieval import get_stock_data
        logger.info("Modules imported successfully")
        
        # Get all stock symbols from database
        logger.info("Connecting to database")
        conn = get_db_connection()
        conn.connect()
        cursor = conn.connection.cursor()
        logger.info("Database connected, executing query")
        
        if days > 0:
            cursor.execute("""
                SELECT s.symbol, s.company_name 
                FROM stock_symbols s
                WHERE EXISTS (
                    SELECT 1 FROM daily_stock_data d 
                    WHERE d.symbol_id = s.id 
                    AND d.date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                )
                ORDER BY s.symbol
            """, (days,))
        else:
            # Get all stocks that have any data
            cursor.execute("""
                SELECT s.symbol, s.company_name 
                FROM stock_symbols s
                WHERE EXISTS (
                    SELECT 1 FROM daily_stock_data d 
                    WHERE d.symbol_id = s.id
                )
                ORDER BY s.symbol
            """)
        
        symbols_data = cursor.fetchall()
        cursor.close()
        conn.connection.close()
        
        logger.info(f"Found {len(symbols_data)} stocks in database")
        if symbols_data:
            # Handle both dict and tuple formats
            if isinstance(symbols_data[0], dict):
                sample_symbols = [s['symbol'] for s in symbols_data[:5]]
            else:
                sample_symbols = [s[0] for s in symbols_data[:5]]
            logger.info(f"Sample symbols: {sample_symbols}")
        
        if not symbols_data:
            logger.info("No symbols found, returning error")
            return jsonify({'error': 'No stocks found in database'}), 404
        
        logger.info(f"Analyzing {len(symbols_data)} stocks for top performers")
        logger.info("About to start analysis loop")
        
        # Analyze each stock
        results = []
        logger.info("Starting first iteration of analysis loop")
        for i, symbol_data in enumerate(symbols_data):
            # Handle both dict and tuple formats
            if isinstance(symbol_data, dict):
                symbol = symbol_data['symbol']
                company_name = symbol_data['company_name']
            else:
                symbol, company_name = symbol_data
            try:
                logger.info(f"Analyzing {i+1}/{len(symbols_data)}: {symbol}")
                
                # Get data for this symbol
                logger.info(f"Calling get_stock_data for {symbol}")
                df = get_stock_data(symbol, days)
                logger.info(f"get_stock_data returned for {symbol}")
                if df is None or len(df) < 30:  # Need minimum data (reduced from 50)
                    logger.debug(f"Skipping {symbol}: insufficient data ({len(df) if df is not None else 0} days)")
                    continue
                
                logger.debug(f"{symbol}: Got {len(df)} days of data")
                
                # Run analysis
                engine = MATradingEngine(
                    initial_capital, atr_period, atr_multiplier, ma_type, 
                    None, None, 10.0, position_sizing_percentage
                )
                analysis = engine.run_analysis(df, symbol)
                
                logger.debug(f"{symbol}: Analysis complete, {len(analysis.trades)} trades")
                
                # Calculate win rate
                total_trades = len(analysis.trades)
                winning_trades = len([t for t in analysis.trades if t.pnl and t.pnl > 0])
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Calculate total return percentage
                if initial_capital == 0:
                    logger.error(f"Initial capital is 0 for {symbol}")
                    continue
                
                # Handle both dict and object formats for performance_metrics
                if isinstance(analysis.performance_metrics, dict):
                    total_pnl = analysis.performance_metrics['total_pnl']
                    sharpe_ratio = analysis.performance_metrics['sharpe_ratio']
                else:
                    total_pnl = analysis.performance_metrics.total_pnl
                    sharpe_ratio = analysis.performance_metrics.sharpe_ratio
                    
                total_return_pct = (total_pnl / initial_capital) * 100
                
                results.append({
                    'symbol': symbol,
                    'company_name': company_name,
                    'total_return_pct': round(total_return_pct, 2),
                    'total_pnl': round(total_pnl, 2),
                    'win_rate': round(win_rate, 1),
                    'total_trades': total_trades,
                    'sharpe_ratio': round(sharpe_ratio, 2)
                })
                
                logger.debug(f"{symbol}: Added to results")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
                continue
        
        # Sort by total return percentage (descending)
        results.sort(key=lambda x: x['total_return_pct'], reverse=True)
        
        # Return top 10
        top_10 = results[:10]
        
        logger.info(f"Top performers analysis complete. Found {len(results)} valid stocks out of {len(symbols_data)} total stocks.")
        if results:
            logger.info(f"Top performer: {results[0]['symbol']} with {results[0]['total_return_pct']}% return")
        
        return jsonify({
            'success': True,
            'top_performers': top_10,
            'total_analyzed': len(results),
            'analysis_params': {
                'days': days,
                'initial_capital': initial_capital,
                'position_sizing_percentage': position_sizing_percentage
            }
        })
        
    except Exception as e:
        logger.error(f"Error in top performers analysis: {e}")
        return jsonify({'error': str(e)}), 500
