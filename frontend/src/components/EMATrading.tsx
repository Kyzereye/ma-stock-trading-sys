import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  LinearProgress,
  Autocomplete,
  Tooltip
} from '@mui/material';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, Time } from 'lightweight-charts';
import { useAuth } from '../contexts/AuthContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:2222';

interface EMASignal {
  date: string;
  signal_type: 'BUY' | 'SELL';
  price: number;
  ma_21: number;
  ma_50: number;
  atr: number;
  trailing_stop: number;
  reasoning: string;
  confidence: number;
}

interface EMATrade {
  entry_date: string;
  exit_date: string | null;
  entry_price: number;
  exit_price: number | null;
  entry_signal: string;
  exit_signal: string;
  exit_reason: string;
  shares: number;
  pnl: number | null;
  pnl_percent: number | null;
  duration_days: number | null;
}

interface EMAPerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_return_percent: number;
  avg_trade_duration: number;
  max_drawdown: number;
  sharpe_ratio: number;
}

interface MeanReversionAlert {
  date: string;
  price: number;
  ma_21: number;
  distance_percent: number;
  reasoning: string;
}

interface EMAResults {
  symbol: string;
  start_date: string;
  end_date: string;
  total_days: number;
  performance_metrics: EMAPerformanceMetrics;
  trades: EMATrade[];
  signals: EMASignal[];
  mean_reversion_alerts: MeanReversionAlert[];
  equity_curve: Array<{ date: string; equity: number }>;
}

const EMATrading: React.FC = () => {
  const { user, token } = useAuth();
  
  const [symbol, setSymbol] = useState('');
  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);
  const [days, setDays] = useState(user?.preferences.default_days || 365);
  const [atrMultiplier, setAtrMultiplier] = useState(user?.preferences.default_atr_multiplier || 2.0);
  const [maType, setMaType] = useState<'ema' | 'sma'>((user?.preferences.default_ma_type as 'ema' | 'sma') || 'ema');
  const [meanReversionThreshold, setMeanReversionThreshold] = useState(user?.preferences.mean_reversion_threshold || 10.0);
  const [tradesColumns, setTradesColumns] = useState(user?.preferences.trades_columns || {
    entry_date: true, exit_date: true, entry_price: true, exit_price: true,
    exit_reason: true, shares: true, pnl: true, pnl_percent: true,
    running_pnl: true, running_capital: true, drawdown: true, duration: true
  });
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<EMAResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  
  // Chart-related state
  const [stockData, setStockData] = useState<any[]>([]);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // Fetch available symbols on mount
  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const response = await fetch(`${API_URL}/api/symbols`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        if (data.symbols) {
          setAvailableSymbols(data.symbols);
        }
      } catch (error) {
        console.error('Failed to fetch symbols:', error);
      }
    };
    fetchSymbols();
  }, [token]);

  // Update parameters when user preferences change
  useEffect(() => {
    if (user?.preferences) {
      setDays(user.preferences.default_days);
      setAtrMultiplier(user.preferences.default_atr_multiplier);
      setMaType(user.preferences.default_ma_type as 'ema' | 'sma');
      setMeanReversionThreshold(user.preferences.mean_reversion_threshold);
      setTradesColumns(user.preferences.trades_columns || {
        entry_date: true, exit_date: true, entry_price: true, exit_price: true,
        exit_reason: true, shares: true, pnl: true, pnl_percent: true,
        running_pnl: true, running_capital: true, drawdown: true, duration: true
      });
    }
  }, [user]);

  const runEMAAnalysis = async () => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(`${API_URL}/api/ema/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: symbol.toUpperCase(),
          initial_capital: user?.preferences.default_initial_capital || 100000,
          days: days,
          atr_period: user?.preferences.default_atr_period || 14,
          atr_multiplier: atrMultiplier,
          ma_type: maType,
          mean_reversion_threshold: meanReversionThreshold,
          position_sizing_percentage: user?.preferences.position_sizing_percentage || 5.0
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to analyze EMA trading');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signalType: string) => {
    return signalType === 'BUY' ? 'success' : 'error';
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'success';
    if (value < 0) return 'error';
    return 'default';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const getExitReasonHeaderTooltip = () => {
    return (
      <div>
        <div><strong>MA Signal:</strong> Price closed below 21 MA (primary exit)</div>
        <div><strong>Trailing Stop:</strong> Hit stop loss (Highest Price - ATR × Multiplier)</div>
        <div><strong>Trend Break:</strong> Price closed below 50 MA (major reversal)</div>
      </div>
    );
  };

  // Chart functions
  const initializeChart = () => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#485563',
      },
      timeScale: {
        borderColor: '#485563',
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    const ma21Series = chart.addLineSeries({
      color: '#ffffff',  // White for fast MA (21)
      lineWidth: 1,
    });

    const ma50Series = chart.addLineSeries({
      color: '#2196f3',  // Blue for slow MA (50)
      lineWidth: 1,
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    ema21SeriesRef.current = ma21Series;
    ema50SeriesRef.current = ma50Series;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  };

  const loadChartData = async () => {
    if (!symbol || !results) return;

    try {
      const response = await fetch(`${API_URL}/api/stocks/${symbol}?days=${days}&include_ema=true&ma_type=${maType}`);
      const data = await response.json();
      
      if (data.success) {
        setStockData(data.data);
      } else {
        console.error('Failed to load chart data:', data.error);
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  const updateChart = () => {
    if (!chartRef.current || !candlestickSeriesRef.current || !ema21SeriesRef.current || !ema50SeriesRef.current || !stockData.length) {
      return;
    }

    // Prepare candlestick data - extract date only (YYYY-MM-DD)
    const candlestickData: CandlestickData[] = stockData
      .map((data) => ({
        time: data.date.split('T')[0] as Time,  // Strip time portion
        open: parseFloat(data.open),
        high: parseFloat(data.high),
        low: parseFloat(data.low),
        close: parseFloat(data.close),
      }))
      .sort((a, b) => (a.time as string).localeCompare(b.time as string));

    // Prepare Moving Average data
    const ma21Data: LineData[] = stockData
      .filter(data => data.ma_21 !== null && data.ma_21 !== undefined)
      .map((data) => ({
        time: data.date.split('T')[0] as Time,  // Strip time portion
        value: parseFloat(data.ma_21),
      }))
      .sort((a, b) => (a.time as string).localeCompare(b.time as string));

    const ma50Data: LineData[] = stockData
      .filter(data => data.ma_50 !== null && data.ma_50 !== undefined)
      .map((data) => ({
        time: data.date.split('T')[0] as Time,  // Strip time portion
        value: parseFloat(data.ma_50),
      }))
      .sort((a, b) => (a.time as string).localeCompare(b.time as string));

    // Prepare signal markers - extract date only (YYYY-MM-DD)
    const signalMarkers: any[] = [];
    if (results && results.signals) {
      results.signals.forEach(signal => {
        const dateStr = signal.date.includes('T') ? signal.date.split('T')[0] : signal.date;
        const marker = {
          time: dateStr as Time,
          position: signal.signal_type === 'BUY' ? 'belowBar' as const : 'aboveBar' as const,
          color: signal.signal_type === 'BUY' ? '#00ff00' : '#ff0000',
          shape: signal.signal_type === 'BUY' ? 'arrowUp' as const : 'arrowDown' as const,
          text: signal.signal_type === 'BUY' ? 'Entry' : 'Exit',
        };
        signalMarkers.push(marker);
      });
    }

    // Add mean reversion alert markers
    if (results && results.mean_reversion_alerts && results.mean_reversion_alerts.length > 0) {
      results.mean_reversion_alerts.forEach(alert => {
        const dateStr = alert.date.includes('T') ? alert.date.split('T')[0] : alert.date;
        const alertMarker = {
          time: dateStr as Time,
          position: 'aboveBar' as const,
          color: '#ffa500', // Orange color for alerts
          shape: 'circle' as const,
          text: `Alert: ${alert.distance_percent.toFixed(1)}%`,
        };
        signalMarkers.push(alertMarker);
      });
    }

    // Update series
    candlestickSeriesRef.current.setData(candlestickData);
    ema21SeriesRef.current.setData(ma21Data);
    ema50SeriesRef.current.setData(ma50Data);
    
    // Sort markers by time to ensure chronological order
    signalMarkers.sort((a, b) => (a.time as string).localeCompare(b.time as string));
    
    // Update signal markers
    candlestickSeriesRef.current.setMarkers(signalMarkers);

    // Fit content
    chartRef.current.timeScale().fitContent();
  };

  // Initialize chart when component mounts
  useEffect(() => {
    if (activeTab === 4) { // Chart tab
      const cleanup = initializeChart();
      return cleanup;
    }
  }, [activeTab]);

  // Load chart data when results change
  useEffect(() => {
    if (results && activeTab === 4) {
      // Add a small delay to ensure chart is initialized
      setTimeout(() => {
        loadChartData();
      }, 100);
    }
  }, [results, activeTab]);

  // Update chart when data changes
  useEffect(() => {
    if (stockData.length > 0 && results && activeTab === 4) {
      // Add a small delay to ensure chart is ready
      setTimeout(() => {
        updateChart();
      }, 100);
    }
  }, [stockData, results, activeTab]);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Moving Average Trading System
      </Typography>
      
      <Typography variant="subtitle1" color="textSecondary" sx={{ mb: 3 }}>
        Simple {maType.toUpperCase()} Strategy: BUY when price closes above 50 {maType.toUpperCase()}, SELL when price closes below 21 {maType.toUpperCase()}
      </Typography>

      {/* Input Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'flex-start' }}>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <Autocomplete
                freeSolo
                openOnFocus={false}
                options={availableSymbols}
                value={symbol}
                onChange={(event, newValue) => {
                  setSymbol(newValue ? newValue.toUpperCase() : '');
                }}
                onInputChange={(event, newInputValue) => {
                  setSymbol(newInputValue.toUpperCase());
                }}
                filterOptions={(options, { inputValue }) => {
                  if (!inputValue) return [];
                  return options.filter((option) =>
                    option.toUpperCase().startsWith(inputValue.toUpperCase())
                  );
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Stock Symbol"
                    placeholder="e.g., AAPL"
                  />
                )}
              />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Days to Analyze"
                type="number"
                value={days === 0 ? '' : days}
                onChange={(e) => {
                  const value = e.target.value === '' ? 0 : parseInt(e.target.value, 10);
                  if (!isNaN(value)) {
                    setDays(value);
                  }
                }}
                inputProps={{ min: 0, max: 2000 }}
                helperText={days === 0 ? "0 = All available data" : "Enter number of days to analyze"}
              />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="ATR Multiplier"
                type="number"
                value={atrMultiplier}
                onChange={(e) => setAtrMultiplier(Number(e.target.value))}
                inputProps={{ min: 0.5, max: 5.0, step: 0.1 }}
                helperText="Stop loss = ATR × Multiplier"
              />
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <TextField
                fullWidth
                select
                label="Moving Average Type"
                value={maType}
                onChange={(e) => setMaType(e.target.value as 'ema' | 'sma')}
                SelectProps={{
                  native: true,
                }}
                helperText="EMA = Exponential, SMA = Simple"
              >
                <option value="ema">EMA (Exponential)</option>
                <option value="sma">SMA (Simple)</option>
              </TextField>
            </Box>
            <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Mean Reversion Threshold"
                type="number"
                value={meanReversionThreshold}
                onChange={(e) => setMeanReversionThreshold(Number(e.target.value))}
                inputProps={{ min: 3, max: 15, step: 0.5 }}
                helperText="Alert when price is X% above 21-MA (overbought)"
              />
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Button
              variant="contained"
              onClick={runEMAAnalysis}
              disabled={loading}
              sx={{ minWidth: '200px', height: '56px' }}
            >
              {loading ? <CircularProgress size={24} /> : 'Run EMA Analysis'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {results && (
        <Box>
          {/* Performance Summary */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Summary - {results.symbol}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Period: {new Date(results.start_date).toLocaleDateString()} to {new Date(results.end_date).toLocaleDateString()} 
                ({results.total_days} days)
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4" color={getPerformanceColor(results.performance_metrics.total_return_percent)}>
                    {formatPercent(results.performance_metrics.total_return_percent)}
                  </Typography>
                  <Typography variant="caption">Total Return</Typography>
                </Box>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4" color={getPerformanceColor(results.performance_metrics.total_pnl)}>
                    {formatCurrency(results.performance_metrics.total_pnl)}
                  </Typography>
                  <Typography variant="caption">Total P&L</Typography>
                </Box>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4">
                    {results.performance_metrics.total_trades}
                  </Typography>
                  <Typography variant="caption">Total Trades</Typography>
                </Box>
                <Box sx={{ flex: '1 1 200px', textAlign: 'center' }}>
                  <Typography variant="h4" color={getPerformanceColor(results.performance_metrics.win_rate - 50)}>
                    {formatPercent(results.performance_metrics.win_rate)}
                  </Typography>
                  <Typography variant="caption">Win Rate</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Tabs for different views */}
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
                <Tab label="Trades" />
                <Tab label="Signals" />
                <Tab label="Mean Reversion Alerts" />
                <Tab label="Performance Details" />
                <Tab label="Chart" />
              </Tabs>
            </Box>

            <CardContent>
              {/* Trades Tab */}
              {activeTab === 0 && (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        {tradesColumns.entry_date && <TableCell>Entry Date</TableCell>}
                        {tradesColumns.exit_date && <TableCell>Exit Date</TableCell>}
                        {tradesColumns.entry_price && <TableCell>Entry Price</TableCell>}
                        {tradesColumns.exit_price && <TableCell>Exit Price</TableCell>}
                        {tradesColumns.exit_reason && (
                          <TableCell>
                            <Tooltip title={getExitReasonHeaderTooltip()} arrow placement="top">
                              <span style={{ cursor: 'help', textDecoration: 'underline dotted' }}>
                                Exit Reason
                              </span>
                            </Tooltip>
                          </TableCell>
                        )}
                        {tradesColumns.shares && <TableCell>Shares</TableCell>}
                        {tradesColumns.pnl && <TableCell>P&L</TableCell>}
                        {tradesColumns.pnl_percent && <TableCell>P&L %</TableCell>}
                        {tradesColumns.running_pnl && <TableCell>Running P&L</TableCell>}
                        {tradesColumns.running_capital && <TableCell>Running Capital</TableCell>}
                        {tradesColumns.drawdown && <TableCell>Drawdown</TableCell>}
                        {tradesColumns.duration && <TableCell>Duration</TableCell>}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.trades.map((trade, index) => {
                        // Calculate running P&L (cumulative profit/loss starting from 0)
                        // Since trades are sorted newest first, we need to calculate from oldest to current
                        const tradesFromOldest = [...results.trades].reverse();
                        const currentTradeIndex = tradesFromOldest.length - 1 - index;
                        const runningPnl = tradesFromOldest
                          .slice(0, currentTradeIndex + 1)
                          .reduce((sum, t) => sum + (t.pnl || 0), 0);
                        
                        // Calculate running capital (initial capital + running P&L)
                        const runningCapital = (user?.preferences.default_initial_capital || 100000) + runningPnl;
                        
                        // Calculate drawdown (peak capital - current capital)
                        const tradesUpToCurrent = tradesFromOldest.slice(0, currentTradeIndex + 1);
                        const initialCap = user?.preferences.default_initial_capital || 100000;
                        const peakCapital = Math.max(
                          initialCap,
                          ...tradesUpToCurrent.map((t, i) => 
                            initialCap + tradesUpToCurrent.slice(0, i + 1).reduce((sum, trade) => sum + (trade.pnl || 0), 0)
                          )
                        );
                        const drawdown = peakCapital - runningCapital;
                        const drawdownPercent = (drawdown / initialCap) * 100;
                        
                        return (
                        <TableRow key={index}>
                          {tradesColumns.entry_date && <TableCell>{new Date(trade.entry_date).toLocaleDateString()}</TableCell>}
                          {tradesColumns.exit_date && (
                            <TableCell>
                              {trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : 'Open'}
                            </TableCell>
                          )}
                          {tradesColumns.entry_price && <TableCell>{formatCurrency(trade.entry_price)}</TableCell>}
                          {tradesColumns.exit_price && (
                            <TableCell>
                              {trade.exit_price ? formatCurrency(trade.exit_price) : 'Open'}
                            </TableCell>
                          )}
                          {tradesColumns.exit_reason && (
                            <TableCell>
                              {trade.exit_reason || 'Open'}
                            </TableCell>
                          )}
                          {tradesColumns.shares && <TableCell>{trade.shares.toLocaleString()}</TableCell>}
                          {tradesColumns.pnl && (
                            <TableCell>
                              {trade.pnl ? (
                                <Chip
                                  label={formatCurrency(trade.pnl)}
                                  color={getPerformanceColor(trade.pnl)}
                                  size="small"
                                />
                              ) : 'Open'}
                            </TableCell>
                          )}
                          {tradesColumns.pnl_percent && (
                            <TableCell>
                              {trade.pnl_percent ? (
                                <Chip
                                  label={formatPercent(trade.pnl_percent)}
                                  color={getPerformanceColor(trade.pnl_percent)}
                                  size="small"
                                />
                              ) : 'Open'}
                            </TableCell>
                          )}
                          {tradesColumns.running_pnl && (
                            <TableCell>
                              <Chip
                                label={formatCurrency(runningPnl)}
                                color={getPerformanceColor(runningPnl)}
                                size="small"
                              />
                            </TableCell>
                          )}
                          {tradesColumns.running_capital && (
                            <TableCell>
                              <Chip
                                label={formatCurrency(runningCapital)}
                                color={getPerformanceColor(runningCapital - initialCap)}
                                size="small"
                              />
                            </TableCell>
                          )}
                          {tradesColumns.drawdown && (
                            <TableCell>
                              <Chip
                                label={`${drawdownPercent.toFixed(1)}%`}
                                color={drawdown > 0 ? "error" : "success"}
                                size="small"
                              />
                            </TableCell>
                          )}
                          {tradesColumns.duration && (
                            <TableCell>
                              {trade.duration_days ? `${trade.duration_days} days` : 'Open'}
                            </TableCell>
                          )}
                        </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* Signals Tab */}
              {activeTab === 1 && (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Signal</TableCell>
                        <TableCell>Price</TableCell>
                        <TableCell>{maType.toUpperCase()} 21</TableCell>
                        <TableCell>{maType.toUpperCase()} 50</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>Reasoning</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.signals.map((signal, index) => (
                        <TableRow key={index}>
                          <TableCell>{new Date(signal.date).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Chip
                              label={signal.signal_type}
                              color={getSignalColor(signal.signal_type)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{formatCurrency(signal.price)}</TableCell>
                          <TableCell>{formatCurrency(signal.ma_21)}</TableCell>
                          <TableCell>{formatCurrency(signal.ma_50)}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <LinearProgress
                                variant="determinate"
                                value={signal.confidence * 100}
                                sx={{ width: 60, mr: 1 }}
                              />
                              <Typography variant="caption">
                                {formatPercent(signal.confidence * 100)}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>{signal.reasoning}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* Mean Reversion Alerts Tab */}
              {activeTab === 2 && (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Price</TableCell>
                        <TableCell>{maType.toUpperCase()} 21</TableCell>
                        <TableCell>Distance %</TableCell>
                        <TableCell>Reasoning</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.mean_reversion_alerts && results.mean_reversion_alerts.length > 0 ? (
                        results.mean_reversion_alerts.map((alert, index) => (
                          <TableRow key={index}>
                            <TableCell>{new Date(alert.date).toLocaleDateString()}</TableCell>
                            <TableCell>${alert.price.toFixed(2)}</TableCell>
                            <TableCell>${alert.ma_21.toFixed(2)}</TableCell>
                            <TableCell>
                              <Chip
                                label={`${alert.distance_percent.toFixed(1)}%`}
                                color="warning"
                                size="small"
                              />
                            </TableCell>
                            <TableCell>{alert.reasoning}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={5} align="center">
                            <Typography variant="body2" color="text.secondary">
                              No mean reversion alerts found for this analysis period.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* Performance Details Tab */}
              {activeTab === 4 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 300px' }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Trading Statistics
                        </Typography>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Total Trades: <strong>{results.performance_metrics.total_trades}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Winning Trades: <strong>{results.performance_metrics.winning_trades}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Losing Trades: <strong>{results.performance_metrics.losing_trades}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Win Rate: <strong>{formatPercent(results.performance_metrics.win_rate)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Avg Trade Duration: <strong>{results.performance_metrics.avg_trade_duration.toFixed(1)} days</strong>
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>
                  
                  <Box sx={{ flex: '1 1 300px' }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Risk Metrics
                        </Typography>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Max Drawdown: <strong>{formatCurrency(results.performance_metrics.max_drawdown)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Sharpe Ratio: <strong>{results.performance_metrics.sharpe_ratio.toFixed(2)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Initial Capital: <strong>{formatCurrency(user?.preferences.default_initial_capital || 100000)}</strong>
                          </Typography>
                        </Box>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            Final Value: <strong>{formatCurrency((user?.preferences.default_initial_capital || 100000) + results.performance_metrics.total_pnl)}</strong>
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>
                </Box>
              )}

              {/* Chart Tab */}
              {activeTab === 4 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    EMA Trading Chart
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Interactive chart showing price action, EMA lines, and buy/sell signals
                  </Typography>
                  
                  {/* Chart container */}
                  <Box sx={{ 
                    height: '600px', 
                    border: '1px solid', 
                    borderColor: 'divider', 
                    borderRadius: 1,
                    bgcolor: 'background.paper'
                  }}>
                    <div 
                      ref={chartContainerRef} 
                      style={{ 
                        width: '100%', 
                        height: '100%',
                        minHeight: '500px'
                      }} 
                    />
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default EMATrading;
