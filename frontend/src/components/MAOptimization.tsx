import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:2222';

interface OptimizationResult {
  fast_ma: number;
  slow_ma: number;
  ma_distance: number;
  total_return_percent: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_trade_duration: number;
  date_range?: string;
}

interface OptimizationResponse {
  symbol: string;
  best_pair: OptimizationResult | null;
  top_5_pairs: OptimizationResult[];
  total_pairs_tested: number;
  summary_stats: {
    avg_return: number;
    max_return: number;
    avg_trades: number;
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

const MAOptimization: React.FC = () => {
  const { user, token } = useAuth();
  
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<OptimizationResponse | null>(null);
  
  // Optimization parameters
  const [symbol, setSymbol] = useState('');
  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);
  const [days, setDays] = useState(user?.preferences.default_days || 365);
  const [fastRange, setFastRange] = useState({ min: 10, max: 20 });
  const [slowRange, setSlowRange] = useState({ min: 20, max: 50 });
  const [minDistance, setMinDistance] = useState(5);
  const [maType, setMaType] = useState<'ema' | 'sma'>((user?.preferences.default_ma_type as 'ema' | 'sma') || 'ema');
  const [initialCapital, setInitialCapital] = useState(user?.preferences.default_initial_capital || 100000);
  const [atrPeriod, setAtrPeriod] = useState(user?.preferences.default_atr_period || 14);
  const [atrMultiplier, setAtrMultiplier] = useState(user?.preferences.default_atr_multiplier || 2.0);

  // Comparison parameters
  const [comparePairs, setComparePairs] = useState('10,20|21,50|30,60');
  const [compareResults, setCompareResults] = useState<any>(null);

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
      setMaType(user.preferences.default_ma_type as 'ema' | 'sma');
      setInitialCapital(user.preferences.default_initial_capital);
      setAtrPeriod(user.preferences.default_atr_period);
      setAtrMultiplier(user.preferences.default_atr_multiplier);
    }
  }, [user]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const runOptimization = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        days: days.toString(),
        fast_range: `${fastRange.min},${fastRange.max}`,
        slow_range: `${slowRange.min},${slowRange.max}`,
        min_distance: minDistance.toString(),
        initial_capital: initialCapital.toString(),
        atr_period: atrPeriod.toString(),
        atr_multiplier: atrMultiplier.toString(),
        ma_type: maType
      });

      const response = await fetch(`${API_URL}/api/optimization/optimize/${symbol}?${params}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Optimization failed');
      }
      
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const runComparison = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        symbol,
        pairs: comparePairs,
        days: days.toString(),
        initial_capital: initialCapital.toString(),
        atr_period: atrPeriod.toString(),
        atr_multiplier: atrMultiplier.toString(),
        ma_type: maType
      });

      const response = await fetch(`${API_URL}/api/optimization/compare-pairs/${symbol}?${params}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Comparison failed');
      }
      
      setCompareResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };


  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const getPerformanceColor = (value: number, type: 'return' | 'sharpe' | 'drawdown') => {
    if (type === 'return') {
      return value > 0 ? 'success' : 'error';
    } else if (type === 'sharpe') {
      return value > 1 ? 'success' : value > 0 ? 'warning' : 'error';
    } else if (type === 'drawdown') {
      return value < -10 ? 'error' : value < -5 ? 'warning' : 'success';
    }
    return 'default';
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="optimization tabs">
          <Tab label="Optimize MA Pairs" {...a11yProps(0)} />
          <Tab label="Compare Pairs" {...a11yProps(1)} />
          <Tab label="Heatmap" {...a11yProps(2)} />
        </Tabs>
      </Box>

      {/* Optimization Tab */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Optimization Parameters
              </Typography>
              
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
                    label="Symbol"
                  />
                )}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Days to Analyze"
                type="number"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>MA Type</InputLabel>
                <Select
                  value={maType}
                  onChange={(e) => setMaType(e.target.value as 'ema' | 'sma')}
                >
                  <MenuItem value="ema">EMA</MenuItem>
                  <MenuItem value="sma">SMA</MenuItem>
                </Select>
              </FormControl>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <TextField
                    fullWidth
                    label="Fast MA Min"
                    type="number"
                    value={fastRange.min}
                    onChange={(e) => setFastRange(prev => ({ ...prev, min: Number(e.target.value) }))}
                  />
                </Box>
                <Box sx={{ flex: 1 }}>
                  <TextField
                    fullWidth
                    label="Fast MA Max"
                    type="number"
                    value={fastRange.max}
                    onChange={(e) => setFastRange(prev => ({ ...prev, max: Number(e.target.value) }))}
                  />
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <TextField
                    fullWidth
                    label="Slow MA Min"
                    type="number"
                    value={slowRange.min}
                    onChange={(e) => setSlowRange(prev => ({ ...prev, min: Number(e.target.value) }))}
                  />
                </Box>
                <Box sx={{ flex: 1 }}>
                  <TextField
                    fullWidth
                    label="Slow MA Max"
                    type="number"
                    value={slowRange.max}
                    onChange={(e) => setSlowRange(prev => ({ ...prev, max: Number(e.target.value) }))}
                  />
                </Box>
              </Box>
              
              <TextField
                fullWidth
                label="Minimum Distance"
                type="number"
                value={minDistance}
                onChange={(e) => setMinDistance(Number(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Initial Capital"
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="ATR Period"
                type="number"
                value={atrPeriod}
                onChange={(e) => setAtrPeriod(Number(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="ATR Multiplier"
                type="number"
                value={atrMultiplier}
                onChange={(e) => setAtrMultiplier(Number(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <Button
                variant="contained"
                onClick={runOptimization}
                disabled={loading}
                fullWidth
                sx={{ mb: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Run Optimization'}
              </Button>
            </Paper>
          </Box>
          
          <Box sx={{ flex: '2 1 600px', minWidth: '600px' }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {results && results.best_pair && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h5" gutterBottom>
                  Best MA Pair: {results.best_pair.fast_ma}, {results.best_pair.slow_ma}
                </Typography>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Performance Summary
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Total Return
                        </Typography>
                        <Typography variant="h6" color={getPerformanceColor(results.best_pair.total_return_percent, 'return') + '.main'}>
                          {formatPercent(results.best_pair.total_return_percent)}
                        </Typography>
                      </Box>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Win Rate
                        </Typography>
                        <Typography variant="h6">
                          {formatPercent(results.best_pair.win_rate)}
                        </Typography>
                      </Box>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Total Trades
                        </Typography>
                        <Typography variant="h6">
                          {results.best_pair.total_trades}
                        </Typography>
                      </Box>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Sharpe Ratio
                        </Typography>
                        <Typography variant="h6" color={getPerformanceColor(results.best_pair.sharpe_ratio, 'sharpe') + '.main'}>
                          {results.best_pair.sharpe_ratio.toFixed(2)}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            )}
            
            {results && results.top_5_pairs && results.top_5_pairs.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Top 5 Performing Pairs
                </Typography>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Fast MA</TableCell>
                        <TableCell>Slow MA</TableCell>
                        <TableCell>Distance</TableCell>
                        <TableCell>Return %</TableCell>
                        <TableCell>Sharpe</TableCell>
                        <TableCell>Max DD</TableCell>
                        <TableCell>Win Rate</TableCell>
                        <TableCell>Trades</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.top_5_pairs.map((pair, index) => (
                        <TableRow key={index}>
                          <TableCell>{pair.fast_ma}</TableCell>
                          <TableCell>{pair.slow_ma}</TableCell>
                          <TableCell>{pair.ma_distance}</TableCell>
                          <TableCell>
                            <Chip
                              label={formatPercent(pair.total_return_percent)}
                              color={getPerformanceColor(pair.total_return_percent, 'return')}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{pair.sharpe_ratio.toFixed(2)}</TableCell>
                          <TableCell>
                            <Chip
                              label={formatPercent(pair.max_drawdown)}
                              color={getPerformanceColor(pair.max_drawdown, 'drawdown')}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{formatPercent(pair.win_rate)}</TableCell>
                          <TableCell>{pair.total_trades}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
            
            {results && results.summary_stats && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Optimization Summary
                </Typography>
                <Card>
                  <CardContent>
                    <Typography variant="body1" gutterBottom>
                      Analyzed {results.total_pairs_tested} MA pair combinations
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Total Pairs Tested
                        </Typography>
                        <Typography variant="h6">
                          {results.total_pairs_tested}
                        </Typography>
                      </Box>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Average Return
                        </Typography>
                        <Typography variant="h6">
                          {formatPercent(results.summary_stats.avg_return)}
                        </Typography>
                      </Box>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Max Return
                        </Typography>
                        <Typography variant="h6">
                          {formatPercent(results.summary_stats.max_return)}
                        </Typography>
                      </Box>
                      <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
                        <Typography variant="body2" color="text.secondary">
                          Average Trades
                        </Typography>
                        <Typography variant="h6">
                          {results.summary_stats.avg_trades.toFixed(1)}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        </Box>
      </TabPanel>

      {/* Comparison Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Compare Specific Pairs
              </Typography>
              
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
                    label="Symbol"
                  />
                )}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="MA Pairs (format: 10,20|21,50|30,60)"
                value={comparePairs}
                onChange={(e) => setComparePairs(e.target.value)}
                sx={{ mb: 2 }}
                helperText="Separate pairs with | and use comma for MA values"
              />
              
              <TextField
                fullWidth
                label="Days to Analyze"
                type="number"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                sx={{ mb: 2 }}
              />
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>MA Type</InputLabel>
                <Select
                  value={maType}
                  onChange={(e) => setMaType(e.target.value as 'ema' | 'sma')}
                >
                  <MenuItem value="ema">EMA</MenuItem>
                  <MenuItem value="sma">SMA</MenuItem>
                </Select>
              </FormControl>
              
              <Button
                variant="contained"
                onClick={runComparison}
                disabled={loading}
                fullWidth
              >
                {loading ? <CircularProgress size={24} /> : 'Compare Pairs'}
              </Button>
            </Paper>
          </Box>
          
          <Box sx={{ flex: '2 1 600px', minWidth: '600px' }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {compareResults && compareResults.results && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Comparison Results
                </Typography>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Fast MA</TableCell>
                        <TableCell>Slow MA</TableCell>
                        <TableCell>Return %</TableCell>
                        <TableCell>Sharpe</TableCell>
                        <TableCell>Max DD</TableCell>
                        <TableCell>Win Rate</TableCell>
                        <TableCell>Trades</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {compareResults.results.map((result: any, index: number) => (
                        <TableRow key={index}>
                          <TableCell>{result.fast_ma}</TableCell>
                          <TableCell>{result.slow_ma}</TableCell>
                          <TableCell>
                            <Chip
                              label={formatPercent(result.total_return_percent)}
                              color={getPerformanceColor(result.total_return_percent, 'return')}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{result.sharpe_ratio.toFixed(2)}</TableCell>
                          <TableCell>
                            <Chip
                              label={formatPercent(result.max_drawdown)}
                              color={getPerformanceColor(result.max_drawdown, 'drawdown')}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{formatPercent(result.win_rate)}</TableCell>
                          <TableCell>{result.total_trades}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </Box>
        </Box>
      </TabPanel>

      {/* Heatmap Tab */}
      <TabPanel value={tabValue} index={2}>
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            Heatmap visualization coming soon...
          </Typography>
        </Box>
      </TabPanel>
    </Box>
  );
};

export default MAOptimization;