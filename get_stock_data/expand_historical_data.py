#!/usr/bin/env python3
"""
Expand Historical Data Collection
Fetches extended historical data for better backtesting (5+ years or maximum available)
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
dotenv_path = os.path.join(backend_dir, '.env')
load_dotenv(dotenv_path)

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))
# Add the backend directory to the path
sys.path.append(backend_dir)

from stock_scraper import StockDataScraper
from utils.database import get_db_connection

def expand_historical_data(period="5y", delay=1.0):
    """
    Expand historical data collection for all symbols
    
    Args:
        period: Time period to fetch ("2y", "5y", "10y", "max")
        delay: Delay between requests (seconds)
    """
    print(f"🚀 Expanding Historical Data Collection")
    print(f"📅 Target Period: {period}")
    print("=" * 60)
    
    # Initialize scraper
    scraper = StockDataScraper()
    
    # Connect to database
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
        print(f"📈 Will fetch {period} of data for each symbol...")
        print()
        
    except Exception as e:
        print(f"❌ Error getting symbols from database: {e}")
        db.disconnect()
        return
    
    try:
        # Get current data range for each symbol
        print(f"\n🔍 Checking current data ranges...")
        current_ranges = {}
        
        for symbol in symbols:
            try:
                # Get symbol ID
                symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
                symbol_result = db.execute_query(symbol_query, (symbol,))
                
                if not symbol_result:
                    print(f"  ⚠️  {symbol}: Not found in database")
                    continue
                
                symbol_id = symbol_result[0]['id']
                
                # Get current date range
                range_query = """
                    SELECT 
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date,
                        COUNT(*) as total_records
                    FROM daily_stock_data 
                    WHERE symbol_id = %s
                """
                range_result = db.execute_query(range_query, (symbol_id,))
                
                if range_result:
                    current_ranges[symbol] = {
                        'symbol_id': symbol_id,
                        'earliest': range_result[0]['earliest_date'],
                        'latest': range_result[0]['latest_date'],
                        'records': range_result[0]['total_records']
                    }
                    print(f"  📊 {symbol}: {range_result[0]['earliest_date']} to {range_result[0]['latest_date']} ({range_result[0]['total_records']} records)")
                else:
                    print(f"  ⚠️  {symbol}: No data found")
                    
            except Exception as e:
                print(f"  ❌ {symbol}: Error checking range - {e}")
        
        print(f"\n🔄 Fetching extended historical data...")
        print("-" * 60)
        
        success_count = 0
        failed_count = 0
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
            
            try:
                # Fetch extended historical data
                print(f"  📥 Fetching {period} of data for {symbol}...")
                df = scraper.get_stock_data(symbol, period=period, delay=delay)
                
                if df is None or df.empty:
                    print(f"  ❌ No data received for {symbol}")
                    failed_count += 1
                    continue
                
                print(f"  📊 Received {len(df)} records from {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
                
                # Check if we got more data than before
                if symbol in current_ranges:
                    current_earliest = current_ranges[symbol]['earliest']
                    new_earliest = df.index[0].date()
                    
                    if new_earliest < current_earliest:
                        print(f"  ✅ Extended data: {new_earliest} vs previous {current_earliest}")
                    else:
                        print(f"  ℹ️  Same or newer start date: {new_earliest}")
                
                # Store in database (will handle duplicates automatically)
                print(f"  💾 Storing data in database...")
                symbol_id = current_ranges[symbol]['symbol_id'] if symbol in current_ranges else None
                
                if symbol_id is None:
                    # Need to get symbol ID first
                    symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
                    symbol_result = db.execute_query(symbol_query, (symbol,))
                    if symbol_result:
                        symbol_id = symbol_result[0]['id']
                
                if symbol_id:
                    stored_count = store_data_in_database(df, symbol_id, db)
                    print(f"  ✅ Stored {stored_count} new records in database")
                else:
                    print(f"  ❌ Could not find symbol ID for {symbol}")
                    failed_count += 1
                    continue
                
                # Update CSV file
                print(f"  📄 Updating CSV file...")
                scraper.save_to_csv(df, symbol)
                print(f"  ✅ Updated {symbol}_historical_data.csv")
                
                success_count += 1
                print(f"  🎉 Successfully processed {symbol}")
                
            except Exception as e:
                print(f"  ❌ Error processing {symbol}: {e}")
                failed_count += 1
        
        # Update combined portfolio CSV
        print(f"\n📊 Updating combined portfolio data...")
        try:
            all_data = {}
            for symbol in symbols:
                try:
                    df = scraper.get_stock_data(symbol, period=period, delay=0)  # No delay for CSV reading
                    if df is not None and not df.empty:
                        all_data[symbol] = df
                except:
                    continue
            
            if all_data:
                scraper.save_multiple_to_csv(all_data, individual_files=False, combined_file="portfolio_extended_data.csv")
                print(f"  ✅ Updated portfolio_extended_data.csv with {len(all_data)} symbols")
        except Exception as e:
            print(f"  ⚠️  Could not update portfolio CSV: {e}")
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"🎉 Historical Data Expansion Complete!")
        print(f"  ✅ Successful: {success_count} symbols")
        print(f"  ❌ Failed: {failed_count} symbols")
        print(f"  📅 Period: {period}")
        print(f"  📊 Total processed: {len(symbols)} symbols")
        
        # Show final data ranges
        print(f"\n📋 Final Data Ranges:")
        print("-" * 40)
        for symbol in symbols:
            if symbol in current_ranges:
                try:
                    range_query = """
                        SELECT 
                            MIN(date) as earliest_date,
                            MAX(date) as latest_date,
                            COUNT(*) as total_records
                        FROM daily_stock_data 
                        WHERE symbol_id = %s
                    """
                    range_result = db.execute_query(range_query, (current_ranges[symbol]['symbol_id'],))
                    
                    if range_result:
                        earliest = range_result[0]['earliest_date']
                        latest = range_result[0]['latest_date']
                        records = range_result[0]['total_records']
                        days = (latest - earliest).days
                        print(f"  📊 {symbol}: {earliest} to {latest} ({records} records, {days} days)")
                except Exception as e:
                    print(f"  ❌ {symbol}: Error getting final range - {e}")
        
    except Exception as e:
        print(f"❌ Error during data expansion: {e}")
    finally:
        db.disconnect()

def store_data_in_database(df, symbol_id, db):
    """
    Store stock data in database using BATCH insert for speed
    
    Args:
        df: DataFrame with stock data
        symbol_id: Database symbol ID
        db: Database connection
        
    Returns:
        Number of records stored
    """
    try:
        # Prepare all data at once for batch insert
        data_batch = []
        
        for index, row in df.iterrows():
            try:
                # Get date from the 'Date' column
                date_val = row['Date']
                
                # Ensure it's a date object
                if hasattr(date_val, 'date'):
                    date_val = date_val.date()
                elif hasattr(date_val, 'to_pydatetime'):
                    date_val = date_val.to_pydatetime().date()
                
                # Add to batch
                data_batch.append((
                    symbol_id,
                    date_val,
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume'])
                ))
                
            except Exception as e:
                print(f"    ⚠️  Error preparing record for {date_val}: {e}")
                continue
        
        if not data_batch:
            print(f"    ⚠️  No valid data to insert")
            return 0
        
        # Single batch insert - MUCH FASTER than individual inserts!
        insert_query = """
            INSERT INTO daily_stock_data (symbol_id, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume)
        """
        
        rows_affected = db.execute_many(insert_query, data_batch)
        return rows_affected
        
    except Exception as e:
        print(f"    ❌ Error storing data: {e}")
        return 0

def main():
    """Main function"""
    print("📈 Historical Data Expansion Tool")
    print("This will fetch extended historical data for better backtesting")
    print()
    
    # Available periods
    periods = {
        "1": "2y",
        "2": "5y", 
        "3": "10y",
        "4": "max"
    }
    
    print("Available time periods:")
    print("1. 2 years")
    print("2. 5 years (recommended for backtesting)")
    print("3. 10 years")
    print("4. Maximum available data")
    print()
    
    # Get user choice
    while True:
        try:
            choice = input("Select period (1-4, or 'q' to quit): ").strip().lower()
            
            if choice == 'q':
                print("Exiting...")
                return
            
            if choice in periods:
                period = periods[choice]
                break
            else:
                print("Invalid choice. Please select 1-4.")
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    
    # Get delay preference
    try:
        delay_input = input("Delay between requests in seconds (default 1.0): ").strip()
        delay = float(delay_input) if delay_input else 1.0
    except ValueError:
        delay = 1.0
    
    print(f"\n🚀 Starting data expansion...")
    print(f"📅 Period: {period}")
    print(f"⏱️  Delay: {delay} seconds")
    print()
    
    # Confirm before proceeding
    try:
        confirm = input("Proceed with data expansion? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return
    
    # Start expansion
    expand_historical_data(period=period, delay=delay)

if __name__ == "__main__":
    main()
