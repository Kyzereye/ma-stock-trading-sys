# MA Stock Trading System

A dedicated Moving Average trading analysis system with ATR-based trailing stops.

## Features

- **EMA Trading Strategy**: 21/50 EMA crossover with ATR-based trailing stops
- **Interactive Charts**: Real-time visualization with buy/sell signals
- **Risk Management**: Dynamic stop losses based on market volatility
- **Comprehensive Analysis**: Trade history, performance metrics, and signal analysis
- **Database Integration**: Uses the same database as KyzeEyeStockLabs

## Architecture

### Backend (Port 5002)
- **Flask API**: RESTful endpoints for EMA analysis
- **EMA Trading Engine**: Core trading logic with ATR calculations
- **Database Integration**: Connects to existing MySQL database

### Frontend (Port 3001)
- **React + TypeScript**: Modern web interface
- **Material-UI**: Professional dark theme
- **Lightweight Charts**: Interactive financial charts
- **Responsive Design**: Works on desktop and mobile

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/ema/analyze/<symbol>` - Run EMA analysis
- `GET /api/ema/signals/<symbol>` - Get trading signals
- `GET /api/ema/summary/<symbol>` - Get trading summary

## Trading Strategy

1. **Buy Signal**: Price closes above 50 EMA
2. **Sell Signal**: Price closes below 21 EMA OR hits trailing stop
3. **Trailing Stop**: 2x ATR below highest price since entry
4. **Risk Management**: Only one trade at a time

## Configuration

- **ATR Period**: Default 14 (adjustable 5-50)
- **ATR Multiplier**: Default 2.0 (adjustable 0.5-5.0)
- **Initial Capital**: Default $100,000
- **Data Range**: All available data by default

## Database

Uses the same MySQL database as KyzeEyeStockLabs:
- `stock_symbols` - Available stock symbols
- `daily_stock_data` - Historical price data
- `technical_indicators` - Calculated indicators (EMA, ATR)

## Development

This project was separated from KyzeEyeStockLabs to focus specifically on Moving Average trading strategies while maintaining database compatibility.
# ma-stock-trading-sys
