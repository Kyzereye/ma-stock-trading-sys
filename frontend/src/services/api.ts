import axios from 'axios';

// API Base URL - use environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:2222';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout for backtest operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for our API responses
export interface StockData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Trade {
  symbol: string;
  entry_date: string;
  exit_date?: string;
  entry_price: number;
  exit_price?: number;
  action: 'BUY' | 'SELL' | 'HOLD';
  shares: number;
  entry_phase: string;
  exit_phase?: string;
  pnl?: number;
  pnl_percent?: number;
  duration_days?: number;
  entry_reasoning: string;
  exit_reasoning?: string;
}


export interface PerformanceMetrics {
  total_return: number;
  total_return_percent: number;
  final_value: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  max_drawdown_percent: number;
  sharpe_ratio: number;
}


export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// API Service Class
class ApiService {
  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await api.get('/health');
      return response.status === 200;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  // Get available symbols
  async getSymbols(): Promise<string[]> {
    try {
      const response = await api.get('/api/stocks/');
      return response.data.data || [];
    } catch (error) {
      console.error('Failed to get symbols:', error);
      throw error;
    }
  }

  // Get stock data for a symbol
  async getStockData(symbol: string, startDate?: string, endDate?: string): Promise<StockData[]> {
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await api.get(`/api/stocks/${symbol}`, { params });
      return response.data.data || [];
    } catch (error) {
      console.error(`Failed to get stock data for ${symbol}:`, error);
      throw error;
    }
  }


}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
