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

export interface WyckoffSignal {
  date: string;
  phase: 'Accumulation' | 'Distribution' | 'Markup' | 'Markdown';
  action: 'BUY' | 'SELL' | 'HOLD';
  price: number;
  volume_ratio: number;
  confidence: number;
  reasoning: string;
  support_level?: number;
  resistance_level?: number;
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

export interface BacktestResult {
  symbol: string;
  start_date: string;
  end_date: string;
  total_days: number;
  trades: Trade[];
  signals: WyckoffSignal[];
  performance_metrics: PerformanceMetrics;
  phase_analysis: {
    phase_counts: Record<string, number>;
    total_signals: number;
  };
  equity_curve: Array<{
    date: string;
    value: number;
  }>;
}

export interface BacktestSummary {
  total_symbols: number;
  successful_backtests: number;
  failed_backtests: number;
  total_initial_capital: number;
  total_final_value: number;
  overall_return_percent: number;
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

  // Run Wyckoff backtest
  async runBacktest(symbol?: string, initialCapital: number = 100000): Promise<{
    summary: BacktestSummary;
    results: BacktestResult[];
  }> {
    try {
      const payload = {
        symbol,
        initial_capital: initialCapital,
      };

      const response = await api.post('/api/backtest/run', payload);
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Backtest failed');
      }

      return {
        summary: response.data.summary,
        results: response.data.results,
      };
    } catch (error) {
      console.error('Failed to run backtest:', error);
      throw error;
    }
  }

  // Get latest backtest results
  async getLatestBacktestResults(): Promise<{
    summary: BacktestSummary;
    results: BacktestResult[];
  }> {
    try {
      const response = await api.get('/api/backtest/results');
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to get backtest results');
      }

      // The API returns the data in report_data
      const reportData = response.data.report_data;
      
      // Transform top_performers to match BacktestResult interface
      const transformedResults = (reportData.top_performers || []).map((performer: any) => ({
        symbol: performer.symbol,
        start_date: reportData.summary.start_date,
        end_date: reportData.summary.end_date,
        total_days: 0, // Not provided in top_performers
        trades: [], // Not provided in top_performers
        signals: [], // Not provided in top_performers
        performance_metrics: {
          total_return: performer.final_value - 100000, // Approximate
          total_return_percent: performer.total_return_percent,
          final_value: performer.final_value,
          total_trades: performer.total_trades,
          winning_trades: Math.round(performer.total_trades * performer.win_rate / 100),
          losing_trades: Math.round(performer.total_trades * (100 - performer.win_rate) / 100),
          win_rate: performer.win_rate,
          avg_win: 0, // Not provided
          avg_loss: 0, // Not provided
          profit_factor: 0, // Not provided
          max_drawdown_percent: performer.max_drawdown_percent,
          sharpe_ratio: performer.sharpe_ratio
        },
        phase_analysis: {
          phase_counts: {},
          total_signals: 0
        },
        equity_curve: []
      }));

      // Transform summary to match BacktestSummary interface
      const transformedSummary: BacktestSummary = {
        total_symbols: reportData.summary.total_symbols || 0,
        successful_backtests: reportData.summary.total_symbols || 0,
        failed_backtests: 0,
        total_initial_capital: reportData.summary.total_initial_capital || 600000,
        total_final_value: reportData.summary.total_final_value || 0,
        overall_return_percent: reportData.summary.total_return_percent || 0
      };


      return {
        summary: transformedSummary,
        results: transformedResults
      };
    } catch (error) {
      console.error('Failed to get latest backtest results:', error);
      // Return empty data structure to prevent crashes
      return { 
        summary: {
          total_symbols: 0,
          successful_backtests: 0,
          failed_backtests: 0,
          total_initial_capital: 0,
          total_final_value: 0,
          overall_return_percent: 0
        } as BacktestSummary, 
        results: [] 
      };
    }
  }

  // Get backtest results for specific symbol
  async getSymbolBacktest(symbol: string): Promise<BacktestResult> {
    try {
      const response = await api.get(`/api/backtest/${symbol}`);
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to get symbol backtest');
      }

      return response.data.backtest_result;
    } catch (error) {
      console.error(`Failed to get backtest for ${symbol}:`, error);
      throw error;
    }
  }

  // Get available backtest reports
  async getAvailableReports(): Promise<Array<{
    filename: string;
    created: string;
    size: number;
  }>> {
    try {
      const response = await api.get('/api/backtest/reports');
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to get available reports');
      }

      return response.data.reports;
    } catch (error) {
      console.error('Failed to get available reports:', error);
      throw error;
    }
  }

  // Get specific backtest report
  async getReport(filename: string): Promise<{
    summary: BacktestSummary;
    results: BacktestResult[];
  }> {
    try {
      const response = await api.get(`/api/backtest/reports/${filename}`);
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to get report');
      }

      return response.data.report_data;
    } catch (error) {
      console.error(`Failed to get report ${filename}:`, error);
      throw error;
    }
  }

  // Get Wyckoff analysis for symbol
  async getWyckoffAnalysis(symbol: string): Promise<any> {
    try {
      const response = await api.post(`/api/wyckoff/${symbol}/analyze`);
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to get Wyckoff analysis');
      }

      return response.data.analysis;
    } catch (error) {
      console.error(`Failed to get Wyckoff analysis for ${symbol}:`, error);
      throw error;
    }
  }

  // Get quick Wyckoff report
  async getWyckoffReport(): Promise<any> {
    try {
      const response = await api.get('/api/wyckoff/report');
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to get Wyckoff report');
      }

      return response.data;
    } catch (error) {
      console.error('Failed to get Wyckoff report:', error);
      // Return empty data structure to prevent crashes
      return {
        success: false,
        analysis_results: [],
        summary: {
          total_symbols: 0,
          successful_analyses: 0,
          failed_analyses: 0
        }
      };
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
