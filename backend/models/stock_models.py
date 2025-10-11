"""
Database models for stock data
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any

class StockSymbol:
    """Model for stock_symbols table"""
    
    def __init__(self, symbol: str, company_name: str = None, market_cap: int = None, 
                 symbol_id: int = None, created_at: datetime = None, updated_at: datetime = None):
        self.id = symbol_id
        self.symbol = symbol.upper()
        self.company_name = company_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'company_name': self.company_name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockSymbol':
        """Create from dictionary"""
        return cls(
            symbol_id=data.get('id'),
            symbol=data.get('symbol'),
            company_name=data.get('company_name')
        )

class DailyStockData:
    """Model for daily_stock_data table"""
    
    def __init__(self, symbol_id: int, date: date, open_price: float = None, 
                 high: float = None, low: float = None, close: float = None,
                 volume: int = None, data_id: int = None, created_at: datetime = None):
        self.id = data_id
        self.symbol_id = symbol_id
        self.date = date
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'symbol_id': self.symbol_id,
            'date': self.date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyStockData':
        """Create from dictionary"""
        return cls(
            data_id=data.get('id'),
            symbol_id=data.get('symbol_id'),
            date=data.get('date'),
            open_price=data.get('open'),
            high=data.get('high'),
            low=data.get('low'),
            close=data.get('close'),
            volume=data.get('volume'),
            created_at=data.get('created_at')
        )

