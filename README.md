# MA Stock Trading System

A comprehensive Moving Average trading analysis and optimization system with ATR-based trailing stops and advanced backtesting capabilities.

## Features

### Trading Analysis
- **EMA/SMA Trading Strategy**: Configurable 21/50 MA crossover with ATR-based trailing stops
- **Interactive Charts**: Real-time candlestick visualization with EMA/SMA overlays and buy/sell signals
- **Risk Management**: Dynamic trailing stop losses based on ATR (Average True Range)
- **Comprehensive Analysis**: Trade history, performance metrics, and detailed signal analysis
- **Flexible Configuration**: Switch between EMA and SMA, adjust ATR periods and multipliers

### MA Pair Optimization
- **Automated Optimization**: Find the best MA pair combinations for any stock
- **Performance Comparison**: Compare multiple MA pairs side-by-side
- **Universal Analysis**: Test MA pairs across multiple symbols to find universal patterns
- **Heatmap Visualization**: Visual representation of MA pair performance
- **Customizable Ranges**: Set custom ranges for fast and slow MAs with minimum distance constraints

### Technical Features
- **Database Integration**: Uses the same database as KyzeEyeStockLabs
- **Shared Data Retrieval**: Consistent data handling across all analysis systems
- **Performance Metrics**: Total return, Sharpe ratio, win rate, profit factor, max drawdown
- **Trade Analytics**: Average trade duration, total trades, winning/losing trade breakdown

## Architecture

### Backend (Port 2222)
- **Flask API**: RESTful endpoints for trading analysis and optimization
- **MA Trading Engine**: Core trading logic supporting both EMA and SMA
- **MA Optimizer**: Advanced optimization engine for finding optimal MA pairs
- **Shared Data Layer**: Unified data retrieval system ensuring consistency
- **Database Integration**: MySQL connection to existing stock database

### Frontend (Port 1111)
- **React + TypeScript**: Modern, type-safe web interface
- **Material-UI**: Professional dark theme with responsive design
- **Lightweight Charts**: Interactive financial charts with technical indicators
- **Tab Navigation**: Separate interfaces for trading analysis and optimization
- **Real-time Updates**: Live chart updates and performance metrics

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- MySQL database (configured in backend/.env)

### Backend Setup

1. Create a `.env` file in the `backend/` directory with the following:
```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_DEBUG=False

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=StockPxLabs

# Email Configuration (SMTP)
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASS=your_email_password
SMTP_FROM=your_email@example.com
SMTP_SECURE=true

# Frontend Configuration
FRONTEND_URL=http://localhost:1111
```

2. Install dependencies and run:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

Backend will run on `http://localhost:2222`

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

Frontend will run on `http://localhost:1111`

## API Endpoints

### Trading Analysis
- `GET /api/health` - Health check
- `GET /api/ema/analyze/<symbol>` - Run MA trading analysis (supports EMA/SMA)
- `GET /api/ema/signals/<symbol>` - Get trading signals only
- `GET /api/ema/summary/<symbol>` - Get trading summary

### MA Optimization
- `GET /api/optimization/optimize/<symbol>` - Find optimal MA pairs for a symbol
- `GET /api/optimization/compare-pairs/<symbol>` - Compare specific MA pairs
- `GET /api/optimization/universal` - Run optimization across multiple symbols
- `GET /api/optimization/heatmap/<symbol>` - Generate performance heatmap data

## Trading Strategy

### Entry Rules
1. **Buy Signal**: Price closes above the slow MA (default: 50 period)
2. **Position Size**: Uses full available capital (configurable)
3. **Initial Stop**: Set at entry price minus (ATR × multiplier)

### Exit Rules
1. **Primary Exit**: Price closes below the fast MA (default: 21 period)
2. **Trailing Stop**: Dynamically adjusts to (highest price since entry) - (ATR × multiplier)
3. **Risk Management**: Only one position at a time

### Optimization Parameters
- **Fast MA Range**: Minimum and maximum periods for fast MA (e.g., 5-30)
- **Slow MA Range**: Minimum and maximum periods for slow MA (e.g., 20-100)
- **Minimum Distance**: Required gap between fast and slow MA (e.g., 10)
- **MA Type**: Choose between EMA (Exponential) or SMA (Simple)

## Configuration

### Trading Parameters
- **Symbol**: Any stock symbol in the database
- **Days to Analyze**: Number of days to backtest (0 = all available data)
- **Initial Capital**: Starting capital for backtesting (default: $100,000)
- **ATR Period**: Period for ATR calculation (default: 14, range: 5-50)
- **ATR Multiplier**: Stop loss distance multiplier (default: 2.0, range: 0.5-5.0)
- **MA Type**: EMA or SMA (default: EMA)

### Optimization Parameters
- **Fast MA Range**: Min/max for fast MA (default: 5-30)
- **Slow MA Range**: Min/max for slow MA (default: 20-100)
- **Min Distance**: Minimum gap between MAs (default: 10)
- **Days**: Historical period to optimize over (default: 365)

## Database Schema

Database: `StockPxLabs`

### Core Tables:
- `stock_symbols` - Available stock symbols and company names
  - `id`, `symbol`, `company_name`
- `daily_stock_data` - Historical OHLCV data
  - `symbol_id`, `date`, `open`, `high`, `low`, `close`, `volume`
- `users` - User authentication and account management
  - `id`, `email`, `password_hash`, `email_verified`, `verification_token`, etc.
- `user_preferences` - User-specific default settings
  - `user_id`, `name`, `default_days`, `default_atr_period`, `default_atr_multiplier`, `default_ma_type`, `default_initial_capital`

### Technical Indicators:
All technical indicators (EMA, SMA, ATR) are calculated on-the-fly using pandas for maximum flexibility.

## Performance Metrics

### Individual Trade Metrics
- Entry/Exit dates and prices
- P&L (absolute and percentage)
- Trade duration
- Stop loss levels

### Overall Performance
- **Total Return %**: Overall profit/loss percentage
- **Sharpe Ratio**: Risk-adjusted return metric
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Max Drawdown**: Largest peak-to-trough decline
- **Average Trade Duration**: Mean holding period

## Development

This project was separated from KyzeEyeStockLabs to focus specifically on Moving Average trading strategies and optimization while maintaining database compatibility.

### Project Structure
```
MAStockTrading/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── app_config.py          # Application configuration
│   ├── routes/
│   │   ├── ema_routes.py      # Trading analysis endpoints
│   │   └── optimization_routes.py  # Optimization endpoints
│   ├── services/
│   │   ├── ema_trading.py     # MA trading engine
│   │   └── ma_optimizer.py    # MA optimization engine
│   └── utils/
│       ├── database.py        # Database connection
│       └── data_retrieval.py  # Shared data retrieval functions
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EMATrading.tsx       # Trading analysis UI
│   │   │   └── MAOptimization.tsx   # Optimization UI
│   │   ├── services/
│   │   │   └── api.ts               # API service layer
│   │   └── App.tsx                  # Main application component
│   └── package.json
└── README.md
```

## Contributing

When contributing, please ensure:
- All systems use the shared data retrieval function (`utils/data_retrieval.py`)
- Code follows existing patterns and structure
- TypeScript types are properly defined
- API responses are consistent with existing endpoints

## License

This project is part of the KyzeEye stock analysis suite.
