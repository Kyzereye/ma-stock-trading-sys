import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:2222';

interface TopPerformer {
  symbol: string;
  company_name: string;
  total_return_pct: number;
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  sharpe_ratio: number;
}

interface TopPerformersResponse {
  success: boolean;
  top_performers: TopPerformer[];
  total_analyzed: number;
  analysis_params: {
    days: number;
    initial_capital: number;
    position_sizing_percentage: number;
  };
}

const TopPerformers: React.FC = () => {
  const { user, token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<TopPerformersResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Analysis parameters
  const [days, setDays] = useState(user?.preferences.default_days || 365);
  const [atrMultiplier, setAtrMultiplier] = useState(user?.preferences.default_atr_multiplier || 2.0);
  const [maType, setMaType] = useState<'ema' | 'sma'>((user?.preferences.default_ma_type as 'ema' | 'sma') || 'ema');

  // Update parameters when user preferences change
  useEffect(() => {
    if (user?.preferences) {
      setDays(user.preferences.default_days);
      setAtrMultiplier(user.preferences.default_atr_multiplier);
      setMaType(user.preferences.default_ma_type as 'ema' | 'sma');
    }
  }, [user?.preferences]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getPerformanceColor = (returnPct: number) => {
    if (returnPct > 20) return 'success';
    if (returnPct > 10) return 'primary';
    if (returnPct > 0) return 'info';
    if (returnPct > -10) return 'warning';
    return 'error';
  };

  const runAnalysis = async () => {
    if (!token) {
      setError('Please log in to run analysis');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(`${API_URL}/api/ema/top-performers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          initial_capital: user?.preferences.default_initial_capital || 100000,
          days: days,
          atr_period: user?.preferences.default_atr_period || 14,
          atr_multiplier: atrMultiplier,
          ma_type: maType,
          position_sizing_percentage: user?.preferences.position_sizing_percentage || 5.0
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to analyze top performers');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Top Performing Stocks
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Analyze all stocks in the database to find the top 10 performers based on total return using your trading strategy.
      </Typography>

      {/* Analysis Parameters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Analysis Parameters
          </Typography>
          
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
            gap: 2, 
            mb: 2 
          }}>
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
            
            <TextField
              fullWidth
              label="ATR Multiplier"
              type="number"
              value={atrMultiplier}
              onChange={(e) => setAtrMultiplier(Number(e.target.value))}
              inputProps={{ min: 0.5, max: 5.0, step: 0.1 }}
              helperText="Multiplier for trailing stop"
            />
            
            <FormControl fullWidth>
              <InputLabel>MA Type</InputLabel>
              <Select
                value={maType}
                onChange={(e) => setMaType(e.target.value as 'ema' | 'sma')}
                label="MA Type"
              >
                <MenuItem value="ema">EMA</MenuItem>
                <MenuItem value="sma">SMA</MenuItem>
              </Select>
            </FormControl>
            
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Button
                variant="contained"
                onClick={runAnalysis}
                disabled={loading}
                fullWidth
                sx={{ height: '56px' }}
              >
                {loading ? <CircularProgress size={24} /> : 'Analyze All Stocks'}
              </Button>
            </Box>
          </Box>
          
          <Typography variant="caption" color="text.secondary">
            Using: {user?.preferences.default_initial_capital ? formatCurrency(user.preferences.default_initial_capital) : '$100,000'} initial capital, 
            {user?.preferences.position_sizing_percentage || 5}% position sizing, 
            {user?.preferences.default_atr_period || 14} day ATR period
          </Typography>
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
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Top 10 Performing Stocks
              </Typography>
              <Chip 
                label={`${results.total_analyzed} stocks analyzed`} 
                color="primary" 
                variant="outlined" 
              />
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Rank</strong></TableCell>
                    <TableCell><strong>Symbol</strong></TableCell>
                    <TableCell><strong>Company</strong></TableCell>
                    <TableCell align="right"><strong>Total Return</strong></TableCell>
                    <TableCell align="right"><strong>Total P&L</strong></TableCell>
                    <TableCell align="right"><strong>Win Rate</strong></TableCell>
                    <TableCell align="right"><strong>Total Trades</strong></TableCell>
                    <TableCell align="right"><strong>Sharpe Ratio</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.top_performers.map((stock, index) => (
                    <TableRow key={stock.symbol} hover>
                      <TableCell>
                        <Chip 
                          label={`#${index + 1}`} 
                          color={index === 0 ? 'success' : index === 1 ? 'primary' : index === 2 ? 'info' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {stock.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {stock.company_name}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${stock.total_return_pct > 0 ? '+' : ''}${stock.total_return_pct}%`}
                          color={getPerformanceColor(stock.total_return_pct)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          color={stock.total_pnl > 0 ? 'success.main' : 'error.main'}
                          fontWeight="medium"
                        >
                          {formatCurrency(stock.total_pnl)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {stock.win_rate}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {stock.total_trades}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {stock.sharpe_ratio}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            {results.top_performers.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  No stocks found with sufficient data for analysis.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default TopPerformers;
