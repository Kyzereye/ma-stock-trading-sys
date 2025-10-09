"""
Optimization Routes for MA Trading System

Provides endpoints for optimizing Moving Average pairs and comparing performance.
"""

from flask import Blueprint, request, jsonify
import logging
from typing import List, Tuple
import json

from services.ma_optimizer import MAOptimizer

logger = logging.getLogger(__name__)

# Create blueprint
optimization_bp = Blueprint('optimization', __name__, url_prefix='/api/optimization')

@optimization_bp.route('/optimize/<symbol>', methods=['GET'])
def optimize_symbol(symbol: str):
    """
    Optimize MA pairs for a specific symbol
    
    Query Parameters:
    - days: Number of days to analyze (default: 365)
    - fast_range: Fast MA range as "min,max" (default: "5,30")
    - slow_range: Slow MA range as "min,max" (default: "20,100")
    - min_distance: Minimum distance between MAs (default: 10)
    - initial_capital: Starting capital (default: 100000)
    - atr_period: ATR period (default: 14)
    - atr_multiplier: ATR multiplier (default: 2.0)
    - ma_type: MA type 'ema' or 'sma' (default: 'ema')
    """
    try:
        # Parse parameters
        days = int(request.args.get('days', 365))
        fast_range_str = request.args.get('fast_range', '5,30')
        slow_range_str = request.args.get('slow_range', '20,100')
        min_distance = int(request.args.get('min_distance', 10))
        initial_capital = float(request.args.get('initial_capital', 100000))
        atr_period = int(request.args.get('atr_period', 14))
        atr_multiplier = float(request.args.get('atr_multiplier', 2.0))
        ma_type = request.args.get('ma_type', 'ema').lower()
        
        # Parse ranges
        fast_range = tuple(map(int, fast_range_str.split(',')))
        slow_range = tuple(map(int, slow_range_str.split(',')))
        
        # Validate parameters
        if fast_range[0] >= fast_range[1]:
            return jsonify({'error': 'Invalid fast_range: min must be less than max'}), 400
        if slow_range[0] >= slow_range[1]:
            return jsonify({'error': 'Invalid slow_range: min must be less than max'}), 400
        if ma_type not in ['ema', 'sma']:
            return jsonify({'error': 'ma_type must be "ema" or "sma"'}), 400
        
        logger.info(f"Optimizing MA pairs for {symbol}")
        
        # Create optimizer
        optimizer = MAOptimizer(
            initial_capital=initial_capital,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            ma_type=ma_type
        )
        
        # Run optimization
        results = optimizer.optimize_ma_pairs(
            symbol=symbol,
            days=days,
            fast_ma_range=fast_range,
            slow_ma_range=slow_range,
            min_distance=min_distance
        )
        
        # Convert to JSON-serializable format
        response = {
            'symbol': results.symbol,
            'optimization_date': results.optimization_date.isoformat(),
            'parameters_used': results.parameters_used,
            'best_pair': {
                'fast_ma': results.best_pair.fast_ma,
                'slow_ma': results.best_pair.slow_ma,
                'ma_distance': results.best_pair.ma_distance,
                'total_return_percent': results.best_pair.total_return_percent,
                'sharpe_ratio': results.best_pair.sharpe_ratio,
                'max_drawdown': results.best_pair.max_drawdown,
                'win_rate': results.best_pair.win_rate,
                'profit_factor': results.best_pair.profit_factor,
                'total_trades': results.best_pair.total_trades,
                'avg_trade_duration': results.best_pair.avg_trade_duration,
                'date_range': results.best_pair.date_range
            } if results.best_pair is not None else None,
            'top_5_pairs': [
                {
                    'fast_ma': pair.fast_ma,
                    'slow_ma': pair.slow_ma,
                    'ma_distance': pair.ma_distance,
                    'total_return_percent': pair.total_return_percent,
                    'sharpe_ratio': pair.sharpe_ratio,
                    'max_drawdown': pair.max_drawdown,
                    'win_rate': pair.win_rate,
                    'profit_factor': pair.profit_factor,
                    'total_trades': pair.total_trades,
                    'avg_trade_duration': pair.avg_trade_duration
                }
                for pair in results.top_5_pairs if pair is not None
            ],
            'total_pairs_tested': len(results.all_results),
            'summary_stats': {
                'avg_return': sum(p.total_return_percent for p in results.all_results if p is not None) / len([p for p in results.all_results if p is not None]) if results.all_results else 0,
                'max_return': max(p.total_return_percent for p in results.all_results if p is not None) if results.all_results else 0,
                'min_return': min(p.total_return_percent for p in results.all_results if p is not None) if results.all_results else 0,
                'avg_sharpe': sum(p.sharpe_ratio for p in results.all_results if p is not None) / len([p for p in results.all_results if p is not None]) if results.all_results else 0,
                'avg_trades': sum(p.total_trades for p in results.all_results if p is not None) / len([p for p in results.all_results if p is not None]) if results.all_results else 0
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error optimizing {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/compare-pairs/<symbol>', methods=['GET'])
def compare_pairs(symbol: str):
    """
    Compare specific MA pairs for a symbol
    
    Query Parameters:
    - pairs: Comma-separated list of MA pairs as "fast,slow" (e.g., "10,20|21,50|30,60")
    - days: Number of days to analyze (default: 365)
    - initial_capital: Starting capital (default: 100000)
    - atr_period: ATR period (default: 14)
    - atr_multiplier: ATR multiplier (default: 2.0)
    - ma_type: MA type 'ema' or 'sma' (default: 'ema')
    """
    try:
        # Parse parameters
        pairs_str = request.args.get('pairs', '10,20|21,50|30,60')
        days = int(request.args.get('days', 365))
        initial_capital = float(request.args.get('initial_capital', 100000))
        atr_period = int(request.args.get('atr_period', 14))
        atr_multiplier = float(request.args.get('atr_multiplier', 2.0))
        ma_type = request.args.get('ma_type', 'ema').lower()
        
        # Parse MA pairs
        ma_pairs = []
        for pair_str in pairs_str.split('|'):
            try:
                fast, slow = map(int, pair_str.split(','))
                if fast >= slow:
                    return jsonify({'error': f'Invalid pair {pair_str}: fast MA must be less than slow MA'}), 400
                ma_pairs.append((fast, slow))
            except ValueError:
                return jsonify({'error': f'Invalid pair format: {pair_str}. Use "fast,slow"'}), 400
        
        if not ma_pairs:
            return jsonify({'error': 'No valid MA pairs provided'}), 400
        
        logger.info(f"Comparing {len(ma_pairs)} MA pairs for {symbol}")
        
        # Create optimizer
        optimizer = MAOptimizer(
            initial_capital=initial_capital,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            ma_type=ma_type
        )
        
        # Run comparison
        results = optimizer.compare_ma_pairs(symbol, ma_pairs, days)
        
        # Convert to JSON-serializable format
        response = {
            'symbol': symbol,
            'pairs_compared': len(results),
            'results': [
                {
                    'fast_ma': result.fast_ma,
                    'slow_ma': result.slow_ma,
                    'ma_distance': result.ma_distance,
                    'total_return_percent': result.total_return_percent,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate,
                    'profit_factor': result.profit_factor,
                    'total_trades': result.total_trades,
                    'avg_trade_duration': result.avg_trade_duration,
                    'date_range': result.date_range
                }
                for result in results if result is not None
            ],
            'best_pair': {
                'fast_ma': results[0].fast_ma,
                'slow_ma': results[0].slow_ma,
                'total_return_percent': results[0].total_return_percent
            } if results and len(results) > 0 and results[0] is not None else None
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error comparing pairs for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/universal-optimization', methods=['GET'])
def universal_optimization():
    """
    Run optimization across multiple symbols to find universal patterns
    
    Query Parameters:
    - symbols: Comma-separated list of symbols (e.g., "AAPL,MSFT,GOOGL")
    - days: Number of days to analyze (default: 365)
    - fast_range: Fast MA range as "min,max" (default: "5,30")
    - slow_range: Slow MA range as "min,max" (default: "20,100")
    - min_distance: Minimum distance between MAs (default: 10)
    - initial_capital: Starting capital (default: 100000)
    - atr_period: ATR period (default: 14)
    - atr_multiplier: ATR multiplier (default: 2.0)
    - ma_type: MA type 'ema' or 'sma' (default: 'ema')
    """
    try:
        # Parse parameters
        symbols_str = request.args.get('symbols', 'AAPL,MSFT,GOOGL')
        symbols = [s.strip().upper() for s in symbols_str.split(',')]
        days = int(request.args.get('days', 365))
        fast_range_str = request.args.get('fast_range', '5,30')
        slow_range_str = request.args.get('slow_range', '20,100')
        min_distance = int(request.args.get('min_distance', 10))
        initial_capital = float(request.args.get('initial_capital', 100000))
        atr_period = int(request.args.get('atr_period', 14))
        atr_multiplier = float(request.args.get('atr_multiplier', 2.0))
        ma_type = request.args.get('ma_type', 'ema').lower()
        
        # Parse ranges
        fast_range = tuple(map(int, fast_range_str.split(',')))
        slow_range = tuple(map(int, slow_range_str.split(',')))
        
        logger.info(f"Running universal optimization for {len(symbols)} symbols")
        
        # Create optimizer
        optimizer = MAOptimizer(
            initial_capital=initial_capital,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            ma_type=ma_type
        )
        
        # Run universal optimization
        results = optimizer.universal_optimization(
            symbols=symbols,
            days=days,
            fast_ma_range=fast_range,
            slow_ma_range=slow_range,
            min_distance=min_distance
        )
        
        # Analyze universal patterns
        all_best_pairs = [summary.best_pair for summary in results.values() if summary.best_pair]
        
        # Find most common optimal pairs
        pair_frequency = {}
        for pair in all_best_pairs:
            pair_key = f"{pair.fast_ma},{pair.slow_ma}"
            if pair_key not in pair_frequency:
                pair_frequency[pair_key] = {
                    'fast_ma': pair.fast_ma,
                    'slow_ma': pair.slow_ma,
                    'count': 0,
                    'avg_return': 0,
                    'symbols': []
                }
            pair_frequency[pair_key]['count'] += 1
            pair_frequency[pair_key]['avg_return'] += pair.total_return_percent
            pair_frequency[pair_key]['symbols'].append(pair.symbol)
        
        # Calculate averages
        for pair_data in pair_frequency.values():
            pair_data['avg_return'] /= pair_data['count']
        
        # Sort by frequency
        most_common_pairs = sorted(pair_frequency.values(), key=lambda x: x['count'], reverse=True)
        
        # Convert to JSON-serializable format
        response = {
            'symbols_analyzed': len(results),
            'total_symbols_requested': len(symbols),
            'successful_optimizations': len([s for s in results.values() if s.best_pair]),
            'parameters_used': {
                'days': days,
                'fast_range': fast_range,
                'slow_range': slow_range,
                'min_distance': min_distance,
                'ma_type': ma_type
            },
            'universal_insights': {
                'most_common_optimal_pairs': most_common_pairs[:10],
                'avg_optimal_fast_ma': sum(p.fast_ma for p in all_best_pairs if p is not None) / len([p for p in all_best_pairs if p is not None]) if all_best_pairs else 0,
                'avg_optimal_slow_ma': sum(p.slow_ma for p in all_best_pairs if p is not None) / len([p for p in all_best_pairs if p is not None]) if all_best_pairs else 0,
                'avg_optimal_distance': sum(p.ma_distance for p in all_best_pairs if p is not None) / len([p for p in all_best_pairs if p is not None]) if all_best_pairs else 0,
                'avg_best_return': sum(p.total_return_percent for p in all_best_pairs if p is not None) / len([p for p in all_best_pairs if p is not None]) if all_best_pairs else 0
            },
            'symbol_results': {
                symbol: {
                    'best_pair': {
                        'fast_ma': summary.best_pair.fast_ma,
                        'slow_ma': summary.best_pair.slow_ma,
                        'total_return_percent': summary.best_pair.total_return_percent,
                        'sharpe_ratio': summary.best_pair.sharpe_ratio,
                        'win_rate': summary.best_pair.win_rate
                    } if summary.best_pair is not None else None,
                    'total_pairs_tested': len(summary.all_results)
                }
                for symbol, summary in results.items()
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in universal optimization: {e}")
        return jsonify({'error': str(e)}), 500

@optimization_bp.route('/heatmap/<symbol>', methods=['GET'])
def generate_heatmap_data(symbol: str):
    """
    Generate data for MA pair performance heatmap
    
    Query Parameters:
    - days: Number of days to analyze (default: 365)
    - fast_range: Fast MA range as "min,max" (default: "5,30")
    - slow_range: Slow MA range as "min,max" (default: "20,100")
    - min_distance: Minimum distance between MAs (default: 10)
    - metric: Performance metric to use ('return', 'sharpe', 'win_rate', 'profit_factor')
    """
    try:
        # Parse parameters
        days = int(request.args.get('days', 365))
        fast_range_str = request.args.get('fast_range', '5,30')
        slow_range_str = request.args.get('slow_range', '20,100')
        min_distance = int(request.args.get('min_distance', 10))
        metric = request.args.get('metric', 'return')
        
        # Parse ranges
        fast_range = tuple(map(int, fast_range_str.split(',')))
        slow_range = tuple(map(int, slow_range_str.split(',')))
        
        # Validate metric
        valid_metrics = ['return', 'sharpe', 'win_rate', 'profit_factor']
        if metric not in valid_metrics:
            return jsonify({'error': f'Invalid metric. Must be one of: {valid_metrics}'}), 400
        
        logger.info(f"Generating heatmap data for {symbol} using {metric} metric")
        
        # Create optimizer
        optimizer = MAOptimizer()
        
        # Run optimization
        results = optimizer.optimize_ma_pairs(
            symbol=symbol,
            days=days,
            fast_ma_range=fast_range,
            slow_ma_range=slow_range,
            min_distance=min_distance
        )
        
        # Create heatmap data
        heatmap_data = []
        for result in results.all_results:
            value = getattr(result, {
                'return': 'total_return_percent',
                'sharpe': 'sharpe_ratio',
                'win_rate': 'win_rate',
                'profit_factor': 'profit_factor'
            }[metric])
            
            heatmap_data.append({
                'fast_ma': result.fast_ma,
                'slow_ma': result.slow_ma,
                'value': value,
                'total_trades': result.total_trades
            })
        
        response = {
            'symbol': symbol,
            'metric': metric,
            'fast_range': fast_range,
            'slow_range': slow_range,
            'heatmap_data': heatmap_data,
            'best_value': max(heatmap_data, key=lambda x: x['value'])['value'] if heatmap_data else 0,
            'worst_value': min(heatmap_data, key=lambda x: x['value'])['value'] if heatmap_data else 0
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error generating heatmap data for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500
