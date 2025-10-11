#!/usr/bin/env python3
"""
Check Data Availability
Check how much historical data is available for each symbol
"""

import sys
import os
from datetime import datetime
import yfinance as yf
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

def check_data_availability():
    """Check available historical data for all symbols"""
    print("🔍 Checking Historical Data Availability")
    print("=" * 60)
    
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
        print(f"🔍 Checking Yahoo Finance data availability...")
        print()
        
    except Exception as e:
        print(f"❌ Error getting symbols from database: {e}")
        db.disconnect()
        return
    finally:
        db.disconnect()
    
    results = {}
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] Checking {symbol}...", end=" ")
        
        try:
            # Get ticker info
            ticker = yf.Ticker(symbol)
            
            # Try to get maximum available data
            hist = ticker.history(period="max")
            
            if hist is None or hist.empty:
                print("❌ No data available")
                results[symbol] = {
                    'available': False,
                    'error': 'No historical data found'
                }
                continue
            
            # Calculate date range
            earliest_date = hist.index[0].date()
            latest_date = hist.index[-1].date()
            total_days = (latest_date - earliest_date).days
            total_years = total_days / 365.25
            
            # Get company info
            info = ticker.info
            company_name = info.get('longName', 'Unknown')
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            
            results[symbol] = {
                'available': True,
                'company_name': company_name,
                'sector': sector,
                'industry': industry,
                'earliest_date': earliest_date,
                'latest_date': latest_date,
                'total_days': total_days,
                'total_years': round(total_years, 1),
                'total_records': len(hist)
            }
            
            print(f"✅ {total_years:.1f} years ({total_days} days, {len(hist)} records)")
            print(f"    📅 {earliest_date} to {latest_date}")
            print(f"    🏢 {company_name}")
            print(f"    🏭 {sector} - {industry}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results[symbol] = {
                'available': False,
                'error': str(e)
            }
        
        print()
    
    # Summary
    print("=" * 60)
    print("📋 DATA AVAILABILITY SUMMARY")
    print("=" * 60)
    
    available_symbols = [s for s, r in results.items() if r.get('available', False)]
    unavailable_symbols = [s for s, r in results.items() if not r.get('available', False)]
    
    print(f"✅ Available: {len(available_symbols)} symbols")
    print(f"❌ Unavailable: {len(unavailable_symbols)} symbols")
    
    if available_symbols:
        print(f"\n📊 AVAILABLE SYMBOLS:")
        print("-" * 40)
        
        # Sort by total years available
        sorted_symbols = sorted(
            [(s, r) for s, r in results.items() if r.get('available', False)],
            key=lambda x: x[1]['total_years'],
            reverse=True
        )
        
        for symbol, data in sorted_symbols:
            print(f"  📈 {symbol}: {data['total_years']} years ({data['total_records']} records)")
            print(f"     📅 {data['earliest_date']} to {data['latest_date']}")
            print(f"     🏢 {data['company_name']}")
            print()
        
        # Statistics
        years_list = [data['total_years'] for data in results.values() if data.get('available', False)]
        records_list = [data['total_records'] for data in results.values() if data.get('available', False)]
        
        print(f"📊 STATISTICS:")
        print(f"  📅 Average years available: {sum(years_list) / len(years_list):.1f}")
        print(f"  📅 Min years: {min(years_list):.1f}")
        print(f"  📅 Max years: {max(years_list):.1f}")
        print(f"  📊 Average records: {sum(records_list) / len(records_list):.0f}")
        print(f"  📊 Total records across all symbols: {sum(records_list):,}")
        
        # Recommendation
        avg_years = sum(years_list) / len(years_list)
        if avg_years >= 5:
            recommendation = "5y (excellent for backtesting)"
        elif avg_years >= 3:
            recommendation = "5y (good for backtesting, some symbols may have less)"
        else:
            recommendation = "max (get all available data)"
        
        print(f"\n💡 RECOMMENDATION:")
        print(f"  🎯 Use period: '{recommendation}'")
        print(f"  📈 This will give you comprehensive data for backtesting")
    
    if unavailable_symbols:
        print(f"\n❌ UNAVAILABLE SYMBOLS:")
        print("-" * 40)
        for symbol in unavailable_symbols:
            error = results[symbol].get('error', 'Unknown error')
            print(f"  ❌ {symbol}: {error}")
    
    print(f"\n✅ Data availability check completed!")

def main():
    """Main function"""
    check_data_availability()

if __name__ == "__main__":
    main()
