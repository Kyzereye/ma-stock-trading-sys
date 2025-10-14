#!/usr/bin/env python3
"""
Fetch 3 Years of Historical Data
Simple script to get 3 years of data for better backtesting
"""

import sys
import os
from datetime import datetime
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
from utils.performance_analyzer import analyze_and_store_performance

def fetch_3year_data():
    """Fetch 3 years of historical data for all symbols"""
    print("🚀 Fetching 3 Years of Historical Data")
    print("=" * 50)
    
    # Initialize scraper
    scraper = StockDataScraper()
    
    # Connect to database first to get symbols
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
            print("💡 Please run the SQL schema file first: mysql -u root -p StockPxLabs < backend/sql_queries.sql")
            db.disconnect()
            return
        
        symbols = [row['symbol'] for row in symbol_results]
        print(f"📊 Found {len(symbols)} symbols in database")
        print(f"📈 Will fetch 3 years of data for each symbol...")
        print()
        
    except Exception as e:
        print(f"❌ Error getting symbols from database: {e}")
        db.disconnect()
        return
    
    try:
        success_count = 0
        failed_count = 0
        
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] Processing {symbol}...")
            
            try:
                # Get symbol ID
                symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
                symbol_result = db.execute_query(symbol_query, (symbol,))
                
                if not symbol_result:
                    print(f"  ❌ Symbol {symbol} not found in database")
                    failed_count += 1
                    continue
                
                symbol_id = symbol_result[0]['id']
                
                # Fetch 3 years of data
                print(f"  📥 Fetching 3 years of data...")
                df = scraper.get_stock_data(symbol, period="3y")
                
                if df is None or df.empty:
                    print(f"  ❌ No data received for {symbol}")
                    failed_count += 1
                    continue
                
                # Handle date display
                start_date = df.index[0].date() if hasattr(df.index[0], 'date') else df.index[0]
                end_date = df.index[-1].date() if hasattr(df.index[-1], 'date') else df.index[-1]
                print(f"  📊 Received {len(df)} records from {start_date} to {end_date}")
                
                # Store in database
                print(f"  💾 Storing in database...")
                stored_count = store_data_in_database(df, symbol_id, db)
                print(f"  ✅ Stored {stored_count} records in database")
                
                # Analyze performance and store metrics
                print(f"  📊 Analyzing performance...")
                analysis_params = {
                    'initial_capital': 100000,
                    'atr_period': 14,
                    'atr_multiplier': 2.0,
                    'ma_type': 'ema',
                    'position_sizing_percentage': 5.0,
                    'days': 365
                }
                analysis_success = analyze_and_store_performance(symbol, df, analysis_params)
                if analysis_success:
                    print(f"  ✅ Performance analysis completed")
                else:
                    print(f"  ⚠️  Performance analysis failed (insufficient data)")
                
                # Update CSV file
                print(f"  📄 Updating CSV file...")
                scraper.save_to_csv(df, symbol)
                print(f"  ✅ Updated {symbol}_historical_data.csv")
                
                success_count += 1
                print(f"  🎉 Successfully processed {symbol}")
                
            except Exception as e:
                print(f"  ❌ Error processing {symbol}: {e}")
                failed_count += 1
            
            print()
        
        # Update combined portfolio CSV
        print("📊 Updating combined portfolio data...")
        try:
            all_data = {}
            for symbol in symbols:
                try:
                    df = scraper.get_stock_data(symbol, period="3y")
                    if df is not None and not df.empty:
                        all_data[symbol] = df
                except:
                    continue
            
            if all_data:
                scraper.save_multiple_to_csv(all_data, individual_files=False, combined_file="portfolio_3year_data.csv")
                print(f"  ✅ Updated portfolio_3year_data.csv with {len(all_data)} symbols")
        except Exception as e:
            print(f"  ⚠️  Could not update portfolio CSV: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("🎉 3-Year Data Fetch Complete!")
        print(f"  ✅ Successful: {success_count} symbols")
        print(f"  ❌ Failed: {failed_count} symbols")
        print(f"  📅 Period: 3 years")
        
        # Show final data ranges
        print(f"\n📋 Final Data Ranges (3 years):")
        print("-" * 40)
        for symbol in symbols:
            try:
                symbol_query = "SELECT id FROM stock_symbols WHERE symbol = %s"
                symbol_result = db.execute_query(symbol_query, (symbol,))
                
                if symbol_result:
                    symbol_id = symbol_result[0]['id']
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
                        earliest = range_result[0]['earliest_date']
                        latest = range_result[0]['latest_date']
                        records = range_result[0]['total_records']
                        days = (latest - earliest).days
                        years = days / 365.25
                        print(f"  📊 {symbol}: {earliest} to {latest} ({records} records, {years:.1f} years)")
            except Exception as e:
                print(f"  ❌ {symbol}: Error getting final range - {e}")
        
        print(f"\n✅ Ready for backtesting with 3 years of data!")
        
    except Exception as e:
        print(f"❌ Error during data fetch: {e}")
    finally:
        db.disconnect()

def store_data_in_database(df, symbol_id, db):
    """Store stock data in database using BATCH insert for speed"""
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
    print("📈 3-Year Historical Data Fetcher")
    print("This will fetch 3 years of data for better backtesting")
    print()
    
    # Confirm before proceeding
    try:
        confirm = input("Fetch 3 years of data for all symbols? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return
    
    # Start fetching
    fetch_3year_data()

if __name__ == "__main__":
    main()
