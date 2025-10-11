#!/usr/bin/env python3
"""
Stock Data Scraper using Yahoo Finance
Gets 1 year of historical data for multiple stocks
"""

import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime

class StockDataScraper:
    def __init__(self, output_dir="csv_files"):
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_symbols_from_file(self, filename="stock_symbols.txt"):
        """
        Load stock symbols from a text file
        
        Args:
            filename (str): Path to file containing stock symbols
            
        Returns:
            list: List of stock symbols
        """
        symbols = []
        
        try:
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        symbols.append(line.upper())
            
            print(f"Loaded {len(symbols)} symbols from {filename}: {', '.join(symbols)}")
            return symbols
            
        except FileNotFoundError:
            print(f"Error: Could not find {filename}")
            return []
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return []
        
    def get_stock_data(self, symbol, period='1y'):
        """
        Get historical stock data for a given symbol using yfinance
        
        Args:
            symbol (str): Stock symbol (e.g., 'A', 'AAPL')
            period (str): Time period - '1y', '6mo', '3mo', '2y', '5y', 'max'
            
        Returns:
            pandas.DataFrame: Historical stock data
        """
        try:
            print(f"Fetching Yahoo Finance data for {symbol} ({period})...")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=period)
            
            if hist.empty:
                print(f"  No data returned for {symbol}")
                return None
            
            # Clean and format the data
            df = self._clean_data(hist)
            
            # Calculate date range
            if not df.empty and 'Date' in df.columns:
                try:
                    min_date = pd.to_datetime(df['Date']).min()
                    max_date = pd.to_datetime(df['Date']).max()
                    date_range = max_date - min_date
                    days = date_range.days
                    print(f"  Successfully retrieved {len(df)} rows spanning {days} days ({days/365:.1f} years)")
                    print(f"  Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
                except:
                    print(f"  Successfully retrieved {len(df)} rows")
            else:
                print(f"  Successfully retrieved {len(df)} rows")
            
            return df
            
        except Exception as e:
            print(f"  Error fetching data for {symbol}: {e}")
            return None
    
    def _clean_data(self, df):
        """Clean and format Yahoo Finance data"""
        if df.empty:
            return df
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Ensure Date column exists and is properly formatted
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        # Round numeric columns to reasonable precision
        numeric_columns = ['Open', 'High', 'Low', 'Close']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        # Sort by date (newest first)
        df = df.sort_values('Date', ascending=False)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def get_multiple_stocks_data(self, symbols, period='1y', delay=1.0):
        """
        Get historical stock data for multiple symbols
        
        Args:
            symbols (list): List of stock symbols (e.g., ['A', 'AAPL', 'GOOGL'])
            period (str): Time period - '1y', '6mo', '3mo', '2y', '5y', 'max'
            delay (float): Delay between requests in seconds (default 1.0)
            
        Returns:
            dict: Dictionary with symbol as key and DataFrame as value
        """
        results = {}
        failed_symbols = []
        
        print(f"Fetching Yahoo Finance data for {len(symbols)} symbols: {', '.join(symbols)}")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
            
            try:
                df = self.get_stock_data(symbol, period)
                if df is not None and not df.empty:
                    results[symbol] = df
                    print(f"✓ Successfully retrieved {len(df)} rows for {symbol}")
                else:
                    failed_symbols.append(symbol)
                    print(f"✗ No data retrieved for {symbol}")
                    
            except Exception as e:
                failed_symbols.append(symbol)
                print(f"✗ Error processing {symbol}: {e}")
            
            # Add delay between requests to be respectful
            if i < len(symbols):
                time.sleep(delay)
        
        # Summary
        print(f"\n--- Summary ---")
        print(f"Successfully processed: {len(results)} symbols")
        if failed_symbols:
            print(f"Failed to process: {len(failed_symbols)} symbols ({', '.join(failed_symbols)})")
        
        return results
    
    def save_to_csv(self, df, symbol, filename=None):
        """Save DataFrame to CSV file in the output directory"""
        if filename is None:
            filename = f"{symbol}_historical_data.csv"
        
        # Create full path in output directory
        filepath = os.path.join(self.output_dir, filename)
        
        df.to_csv(filepath, index=False)
        print(f"Data saved to {filepath}")
        return filepath
    
    def save_multiple_to_csv(self, stock_data_dict, individual_files=True, combined_file=None):
        """
        Save multiple stock data to CSV files
        
        Args:
            stock_data_dict (dict): Dictionary with symbol as key and DataFrame as value
            individual_files (bool): Save individual CSV files for each stock
            combined_file (str): Optional filename for combined CSV file
            
        Returns:
            list: List of saved filenames
        """
        saved_files = []
        
        # Save individual files
        if individual_files:
            for symbol, df in stock_data_dict.items():
                filename = self.save_to_csv(df, symbol)
                saved_files.append(filename)
        
        # Save combined file
        if combined_file:
            combined_data = []
            for symbol, df in stock_data_dict.items():
                df_copy = df.copy()
                df_copy['Symbol'] = symbol
                combined_data.append(df_copy)
            
            if combined_data:
                combined_df = pd.concat(combined_data, ignore_index=True)
                # Sort by symbol and then by date
                combined_df = combined_df.sort_values(['Symbol', 'Date'], ascending=[True, False])
                
                # Create full path in output directory
                combined_filepath = os.path.join(self.output_dir, combined_file)
                combined_df.to_csv(combined_filepath, index=False)
                print(f"Combined data saved to {combined_filepath}")
                saved_files.append(combined_filepath)
        
        return saved_files
    
    def save_to_csv_append(self, df, symbol, filename=None):
        """Append new data to existing CSV file (preserves existing data)"""
        if filename is None:
            filename = f"{symbol}_historical_data.csv"
        
        # Create full path in output directory
        filepath = os.path.join(self.output_dir, filename)
        
        # Check if file exists
        if os.path.exists(filepath):
            # Read existing data
            existing_df = pd.read_csv(filepath)
            existing_df['Date'] = pd.to_datetime(existing_df['Date']).dt.date
            
            # Filter out dates that already exist
            new_df = df[~df['Date'].isin(existing_df['Date'])]
            
            if new_df.empty:
                print(f"No new data to append for {symbol}")
                return filepath
            
            # Combine existing and new data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.sort_values('Date', ascending=False)
            combined_df.to_csv(filepath, index=False)
            print(f"Appended {len(new_df)} new rows to {filepath}")
        else:
            # File doesn't exist, create new one
            df.to_csv(filepath, index=False)
            print(f"Created new file {filepath}")
        
        return filepath
    
    def save_multiple_to_csv_append(self, stock_data_dict, combined_file=None):
        """
        Append new data to CSV files (preserves existing data)
        
        Args:
            stock_data_dict (dict): Dictionary with symbol as key and DataFrame as value
            combined_file (str): Optional filename for combined CSV file
            
        Returns:
            list: List of updated filenames
        """
        updated_files = []
        
        # Append to individual files
        for symbol, df in stock_data_dict.items():
            filename = self.save_to_csv_append(df, symbol)
            updated_files.append(filename)
        
        # Handle combined file
        if combined_file:
            combined_filepath = os.path.join(self.output_dir, combined_file)
            
            if os.path.exists(combined_filepath):
                # Read existing combined data
                existing_df = pd.read_csv(combined_filepath)
                existing_df['Date'] = pd.to_datetime(existing_df['Date']).dt.date
                
                # Prepare new combined data
                new_combined_data = []
                for symbol, df in stock_data_dict.items():
                    df_copy = df.copy()
                    df_copy['Symbol'] = symbol
                    new_combined_data.append(df_copy)
                
                if new_combined_data:
                    new_combined_df = pd.concat(new_combined_data, ignore_index=True)
                    new_combined_df['Date'] = pd.to_datetime(new_combined_df['Date']).dt.date
                    
                    # Filter out existing combinations of symbol + date
                    existing_combined = existing_df[['Symbol', 'Date']]
                    new_combined_df = new_combined_df[~new_combined_df[['Symbol', 'Date']].apply(tuple, axis=1).isin(existing_combined.apply(tuple, axis=1))]
                    
                    if not new_combined_df.empty:
                        # Combine and sort
                        final_combined = pd.concat([existing_df, new_combined_df], ignore_index=True)
                        final_combined = final_combined.sort_values(['Symbol', 'Date'], ascending=[True, False])
                        final_combined.to_csv(combined_filepath, index=False)
                        print(f"Appended {len(new_combined_df)} new rows to {combined_filepath}")
                    else:
                        print(f"No new data to append to {combined_filepath}")
                else:
                    print(f"No new data to append to {combined_filepath}")
            else:
                # Create new combined file
                combined_data = []
                for symbol, df in stock_data_dict.items():
                    df_copy = df.copy()
                    df_copy['Symbol'] = symbol
                    combined_data.append(df_copy)
                
                if combined_data:
                    combined_df = pd.concat(combined_data, ignore_index=True)
                    combined_df = combined_df.sort_values(['Symbol', 'Date'], ascending=[True, False])
                    combined_df.to_csv(combined_filepath, index=False)
                    print(f"Created new combined file {combined_filepath}")
            
            updated_files.append(combined_filepath)
        
        return updated_files

def main():
    """Example usage of the Yahoo Finance scraper"""
    scraper = StockDataScraper()
    
    # Load stock symbols from file
    symbols = scraper.load_symbols_from_file("stock_symbols.txt")
    
    if not symbols:
        print("No symbols loaded. Please check stock_symbols.txt file.")
        return
    
    print(f"Fetching 1 year of data for {len(symbols)} stocks...")
    stock_data = scraper.get_multiple_stocks_data(symbols, period='1y')
    
    if stock_data:
        print(f"\n=== Results ===")
        for symbol, df in stock_data.items():
            if not df.empty:
                print(f"{symbol}: {len(df)} rows")
            
        # Save individual files
        scraper.save_multiple_to_csv(stock_data, individual_files=True)
        
        # Save combined file
        scraper.save_multiple_to_csv(stock_data, individual_files=False, combined_file="portfolio_1year.csv")
        
        print(f"\n✅ Successfully retrieved 1 year of data for {len(stock_data)} stocks!")
        print(f"Files saved to: {scraper.output_dir}/ directory")
    else:
        print("Failed to retrieve data")

if __name__ == "__main__":
    main()