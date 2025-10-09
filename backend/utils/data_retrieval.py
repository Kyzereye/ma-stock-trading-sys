"""
Shared data retrieval utilities for stock data
"""

import pandas as pd
from typing import Optional
from utils.database import get_db_connection
import logging

logger = logging.getLogger(__name__)

def get_stock_data(symbol: str, days: int) -> Optional[pd.DataFrame]:
    """
    Get stock data from database - shared method used by both EMA analysis and MA optimizer
    
    Args:
        symbol: Stock symbol to retrieve data for
        days: Number of days to retrieve (0 means all data)
    
    Returns:
        DataFrame with stock data or None if no data found
    """
    try:
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
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting stock data for {symbol}: {e}")
        return None
