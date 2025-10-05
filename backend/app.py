#!/usr/bin/env python3
"""
MA Stock Trading Backend
Flask application for Moving Average trading analysis
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from routes.ema_routes import ema_bp
from app_config import Config
from utils.database import get_db_connection
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for frontend
    CORS(app, origins=['http://localhost:1111', 'http://127.0.0.1:1111'])
    
    # Register blueprints
    app.register_blueprint(ema_bp)
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'MA Stock Trading Backend',
            'version': '1.0.0'
        })
    
    @app.route('/api/stocks/<symbol>')
    def get_stock_data(symbol):
        """Get stock data for charting"""
        try:
            days = int(request.args.get('days', 365))
            include_ema = request.args.get('include_ema', 'false').lower() == 'true'
            
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
                ORDER BY d.date ASC 
                LIMIT %s
                """
                cursor.execute(query, (symbol.upper(), days))
            else:
                query = """
                SELECT d.date, d.open, d.high, d.low, d.close, d.volume 
                FROM daily_stock_data d
                JOIN stock_symbols s ON d.symbol_id = s.id
                WHERE s.symbol = %s 
                ORDER BY d.date ASC
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
            df = df.sort_values('date')  # Sort by date ascending for chart
            
            # Convert price columns to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Calculate Moving Averages if requested
            if include_ema:
                ma_type = request.args.get('ma_type', 'ema').lower()
                
                if ma_type == 'sma':
                    df['ma_21'] = df['close'].rolling(window=21).mean()
                    df['ma_50'] = df['close'].rolling(window=50).mean()
                else:  # default to ema
                    df['ma_21'] = df['close'].ewm(span=21).mean()
                    df['ma_50'] = df['close'].ewm(span=50).mean()
            
            # Convert to list of dictionaries for JSON response
            chart_data = []
            for _, row in df.iterrows():
                data_point = {
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                }
                if include_ema:
                    # Handle NaN values by converting to None (which becomes null in JSON)
                    ma_21_val = row['ma_21']
                    ma_50_val = row['ma_50']
                    data_point['ma_21'] = float(ma_21_val) if pd.notna(ma_21_val) else None
                    data_point['ma_50'] = float(ma_50_val) if pd.notna(ma_50_val) else None
                chart_data.append(data_point)
            
            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'data': chart_data
            })
            
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'service': 'MA Stock Trading API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'stock_data': '/api/stocks/<symbol>',
                'ema_analysis': '/api/ema/analyze/<symbol>',
                'ema_signals': '/api/ema/signals/<symbol>',
                'ema_summary': '/api/ema/summary/<symbol>'
            }
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting MA Stock Trading Backend...")
    app.run(host='0.0.0.0', port=2222, debug=True)
