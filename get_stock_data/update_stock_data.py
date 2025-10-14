#!/usr/bin/env python3
"""
Update stock data - fetch new data and update both database and CSV files
Handles duplicates automatically
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
dotenv_path = os.path.join(backend_dir, '.env')
load_dotenv(dotenv_path)

# Add the backend directory to the path
sys.path.append(backend_dir)

from stock_scraper import StockDataScraper
from utils.database import get_db_connection
from utils.performance_analyzer import analyze_and_store_performance

def get_last_update_date(symbol_id, db):
    """Get the last date we have data for a symbol"""
    query = "SELECT MAX(date) as last_date FROM daily_stock_data WHERE symbol_id = %s"
    result = db.execute_query(query, (symbol_id,))
    
    if result and result[0]['last_date']:
        return result[0]['last_date']
    return None

def update_database_data(stock_data_dict, db):
    """Add new stock data to database (only inserts new dates, no updates)"""
    updated_count = 0
    new_count = 0
    
    for symbol, df in stock_data_dict.items():
        print(f"📊 Updating {symbol} in database...")
        
        # Get symbol ID
        symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
        symbol_result = db.execute_query(symbol_query, (symbol.upper(),))
        
        if not symbol_result:
            print(f"  ⚠️  Symbol {symbol} not found in database, skipping...")
            continue
            
        symbol_id = symbol_result[0]['id']
        
        # Get last update date
        last_date = get_last_update_date(symbol_id, db)
        if last_date:
            print(f"  📅 Last data: {last_date}")
        
        # Filter out dates that already exist in database
        existing_dates_query = "SELECT date FROM daily_stock_data WHERE symbol_id = %s"
        existing_dates_result = db.execute_query(existing_dates_query, (symbol_id,))
        existing_dates = set()
        
        if existing_dates_result:
            existing_dates = {row['date'] for row in existing_dates_result}
        
        # Prepare data for insertion (only new dates) - with proper type conversion
        data_to_insert = []
        for _, row in df.iterrows():
            date_val = row['Date']
            
            # Ensure date is proper type
            if hasattr(date_val, 'date'):
                date_val = date_val.date()
            elif hasattr(date_val, 'to_pydatetime'):
                date_val = date_val.to_pydatetime().date()
            
            if date_val not in existing_dates:
                data_to_insert.append((
                    symbol_id,
                    date_val,
                    float(row.get('Open')),
                    float(row.get('High')),
                    float(row.get('Low')),
                    float(row.get('Close')),
                    int(row.get('Volume'))
                ))
        
        if not data_to_insert:
            print(f"  📅 No new dates to add for {symbol}")
            continue
        
        # Insert only new data (no updates)
        insert_query = """
            INSERT INTO daily_stock_data (symbol_id, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        # Insert new data only
        rows_affected = db.execute_many(insert_query, data_to_insert)
        updated_count += rows_affected
        print(f"  ✅ Updated {rows_affected} rows for {symbol}")
    
    return updated_count

def update_csv_files(stock_data_dict, scraper):
    """Append new data to CSV files (preserves existing data)"""
    print(f"\n💾 Updating CSV files (appending new data only)...")
    
    # Update individual CSV files (append new data only)
    for symbol, df in stock_data_dict.items():
        csv_file = scraper.save_to_csv_append(df, symbol)
        print(f"  ✅ Appended new data to {csv_file}")
    
    # Update combined portfolio file (append new data)
    scraper.save_multiple_to_csv_append(
        stock_data_dict, 
        combined_file="portfolio_1year_data.csv"
    )
    print(f"  ✅ Appended new data to portfolio_1year_data.csv")

def main():
    """Update stock data in both database and CSV files"""
    print("🔄 Stock Data Updater")
    print("=" * 50)
    
    # Create scraper
    scraper = StockDataScraper()
    
    # Connect to database to get symbols
    db = get_db_connection()
    if not db.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Get all symbols from database
        symbol_query = "SELECT symbol FROM stock_symbols ORDER BY symbol"
        symbol_results = db.execute_query(symbol_query)
        
        if not symbol_results:
            print("❌ No symbols found in database")
            db.disconnect()
            return
        
        symbols = [row['symbol'] for row in symbol_results]
        print(f"📊 Found {len(symbols)} symbols in database")
        print(f"📈 Fetching latest data for all symbols...")
        print()
        
    except Exception as e:
        print(f"❌ Error getting symbols from database: {e}")
        db.disconnect()
        return
    finally:
        db.disconnect()
    
    # Get fresh data for all symbols
    stock_data = scraper.get_multiple_stocks_data(symbols, period='1y', delay=1.0)
    
    if not stock_data:
        print("❌ Failed to retrieve any stock data")
        return
    
    print(f"\n✅ Successfully retrieved fresh data for {len(stock_data)} stocks")
    
    # Print summary of what we got
    for symbol, df in stock_data.items():
        if not df.empty and 'Date' in df.columns:
            min_date = df['Date'].min()
            max_date = df['Date'].max()
            print(f"  📊 {symbol}: {len(df)} rows ({min_date} to {max_date})")
        else:
            print(f"  ❌ {symbol}: No data")
    
    # Connect to database
    db = get_db_connection()
    if not db.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Update database (handles duplicates automatically)
        print(f"\n🗄️  Updating database...")
        total_updated = update_database_data(stock_data, db)
        print(f"✅ Database updated: {total_updated} total rows affected")
        
        # Update performance metrics for all symbols
        print(f"\n📊 Updating performance metrics...")
        analysis_params = {
            'initial_capital': 100000,
            'atr_period': 14,
            'atr_multiplier': 2.0,
            'ma_type': 'ema',
            'position_sizing_percentage': 5.0,
            'days': 365
        }
        
        analysis_success_count = 0
        for symbol, df in stock_data.items():
            if df is not None and not df.empty:
                try:
                    success = analyze_and_store_performance(symbol, df, analysis_params)
                    if success:
                        analysis_success_count += 1
                except Exception as e:
                    print(f"  ⚠️  Performance analysis failed for {symbol}: {e}")
        
        print(f"✅ Performance metrics updated: {analysis_success_count}/{len(stock_data)} symbols")
        
        # Update CSV files (overwrites existing)
        update_csv_files(stock_data, scraper)
        
        print(f"\n🎉 Update completed successfully!")
        print(f"   📊 Database: {total_updated} new rows added (no updates, no duplicates)")
        print(f"   💾 CSV files: New data appended (existing data preserved)")
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
