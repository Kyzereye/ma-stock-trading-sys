import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Divider,
  Alert,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Chip,
  InputAdornment,
  Checkbox,
  FormControlLabel
} from '@mui/material';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:2222';

interface UserProfileProps {
  open: boolean;
  onClose: () => void;
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
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const UserProfile: React.FC<UserProfileProps> = ({ open, onClose }) => {
  const { user, token, refreshUser } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Profile fields
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');

  // Password fields
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');

  // Preference fields
  const [defaultDays, setDefaultDays] = useState(user?.preferences.default_days || 365);
  const [defaultAtrPeriod, setDefaultAtrPeriod] = useState(user?.preferences.default_atr_period || 14);
  const [defaultAtrMultiplier, setDefaultAtrMultiplier] = useState(user?.preferences.default_atr_multiplier || 2.0);
  const [defaultMaType, setDefaultMaType] = useState(user?.preferences.default_ma_type || 'ema');
  const [defaultInitialCapital, setDefaultInitialCapital] = useState(user?.preferences.default_initial_capital || 100000);
  const [meanReversionThreshold, setMeanReversionThreshold] = useState(user?.preferences.mean_reversion_threshold || 10.0);
  const [positionSizingPercentage, setPositionSizingPercentage] = useState(user?.preferences.position_sizing_percentage || 5.0);
  const [tradesColumns, setTradesColumns] = useState(user?.preferences.trades_columns || {
    entry_date: true, exit_date: true, entry_price: true, exit_price: true,
    exit_reason: true, shares: true, pnl: true, pnl_percent: true,
    running_pnl: true, running_capital: true, drawdown: true, duration: true
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setMessage(null);
  };

  const handleUpdateProfile = async () => {
    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name, email })
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: 'Profile updated successfully!' });
        
        // Update user data in localStorage
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          if (name) userData.name = name;
          if (email) userData.email = email;
          localStorage.setItem('user', JSON.stringify(userData));
        }
        
        // Reload page to refresh context
        setTimeout(() => {
          window.location.reload();
        }, 500);
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to update profile' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update profile' });
    }

    setLoading(false);
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmNewPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/auth/change-password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: 'Password changed successfully!' });
        setCurrentPassword('');
        setNewPassword('');
        setConfirmNewPassword('');
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to change password' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to change password' });
    }

    setLoading(false);
  };

  const handleUpdatePreferences = async (customTradesColumns?: any) => {
    setLoading(true);
    setMessage(null);

    try {
      // Check if customTradesColumns is an event object and filter it out
      const validTradesColumns = customTradesColumns && 
        typeof customTradesColumns === 'object' && 
        !customTradesColumns.nativeEvent ? customTradesColumns : undefined;
      
      const requestData = {
        default_days: defaultDays,
        default_atr_period: defaultAtrPeriod,
        default_atr_multiplier: defaultAtrMultiplier,
        default_ma_type: defaultMaType,
        default_initial_capital: defaultInitialCapital,
        mean_reversion_threshold: meanReversionThreshold,
        position_sizing_percentage: positionSizingPercentage,
        ...(validTradesColumns && { trades_columns: validTradesColumns })
      };
      
      console.log('Sending to backend:', requestData);
      
      const response = await fetch(`${API_URL}/api/auth/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();
      console.log('Backend response:', data);
      console.log('Response status:', response.status);
      console.log('data.success:', data.success);
      console.log('typeof data.success:', typeof data.success);

      if (data.success === true || data.success === 'true') {
        setMessage({ type: 'success', text: 'Preferences saved successfully!' });
        
        // Update user data in localStorage with the actual data that was sent
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          userData.preferences = {
            ...userData.preferences, // Keep existing preferences
            default_days: requestData.default_days,
            default_atr_period: requestData.default_atr_period,
            default_atr_multiplier: requestData.default_atr_multiplier,
            default_ma_type: requestData.default_ma_type,
            default_initial_capital: requestData.default_initial_capital,
            mean_reversion_threshold: requestData.mean_reversion_threshold,
            position_sizing_percentage: requestData.position_sizing_percentage,
            ...(requestData.trades_columns && { trades_columns: requestData.trades_columns })
          };
          localStorage.setItem('user', JSON.stringify(userData));
          console.log('Updated localStorage:', userData.preferences);
          // Refresh the user context to update all components
          refreshUser();
        }
        
        // No need to reload page since we're refreshing the user context
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to save preferences' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save preferences' });
    }

    setLoading(false);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">User Profile</Typography>
          <Chip label={user?.role_display || 'Free'} color="primary" size="small" />
        </Box>
      </DialogTitle>

      <Tabs value={tabValue} onChange={handleTabChange} centered>
        <Tab label="Account" />
        <Tab label="Password" />
        <Tab label="Trading Preferences" />
        <Tab label="Column Preferences" />
      </Tabs>

      <DialogContent>
        {message && (
          <Alert severity={message.type} sx={{ mb: 2 }}>
            {message.text}
          </Alert>
        )}

        {/* Account Tab */}
        <TabPanel value={tabValue} index={0}>
          <TextField
            fullWidth
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
          />
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              onClick={handleUpdateProfile}
              disabled={loading}
            >
              Update Profile
            </Button>
          </Box>
        </TabPanel>

        {/* Password Tab */}
        <TabPanel value={tabValue} index={1}>
          <TextField
            fullWidth
            label="Current Password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            margin="normal"
            helperText="Min 11 characters, uppercase, lowercase, number, special character"
          />
          <TextField
            fullWidth
            label="Confirm New Password"
            type="password"
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
            margin="normal"
          />
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              onClick={handleChangePassword}
              disabled={loading || !currentPassword || !newPassword || !confirmNewPassword}
            >
              Change Password
            </Button>
          </Box>
        </TabPanel>

        {/* Trading Preferences Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>
              Default Analysis Period: {defaultDays} days
            </Typography>
            <Slider
              value={defaultDays}
              onChange={(e, value) => setDefaultDays(value as number)}
              min={30}
              max={1095}
              step={30}
              marks={[
                { value: 30, label: '30d' },
                { value: 365, label: '1y' },
                { value: 730, label: '2y' },
                { value: 1095, label: '3y' }
              ]}
              valueLabelDisplay="auto"
            />
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>
              ATR Period: {defaultAtrPeriod}
            </Typography>
            <Slider
              value={defaultAtrPeriod}
              onChange={(e, value) => setDefaultAtrPeriod(value as number)}
              min={5}
              max={50}
              marks={[
                { value: 5, label: '5' },
                { value: 14, label: '14' },
                { value: 30, label: '30' },
                { value: 50, label: '50' }
              ]}
              valueLabelDisplay="auto"
            />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>
              ATR Multiplier: {defaultAtrMultiplier}
            </Typography>
            <Slider
              value={defaultAtrMultiplier}
              onChange={(e, value) => setDefaultAtrMultiplier(value as number)}
              min={0.5}
              max={5.0}
              step={0.1}
              marks={[
                { value: 0.5, label: '0.5' },
                { value: 2.0, label: '2.0' },
                { value: 5.0, label: '5.0' }
              ]}
              valueLabelDisplay="auto"
            />
          </Box>

          <Divider sx={{ my: 2 }} />

          <FormControl fullWidth margin="normal">
            <InputLabel>Default MA Type</InputLabel>
            <Select
              value={defaultMaType}
              label="Default MA Type"
              onChange={(e) => setDefaultMaType(e.target.value)}
            >
              <MenuItem value="ema">EMA (Exponential Moving Average)</MenuItem>
              <MenuItem value="sma">SMA (Simple Moving Average)</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Default Initial Capital"
            type="number"
            value={defaultInitialCapital}
            onChange={(e) => setDefaultInitialCapital(Number(e.target.value))}
            margin="normal"
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
            }}
          />

          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>
              Mean Reversion Threshold: {meanReversionThreshold}%
            </Typography>
            <Slider
              value={meanReversionThreshold}
              onChange={(e, value) => setMeanReversionThreshold(value as number)}
              min={3}
              max={15}
              step={0.5}
              marks={[
                { value: 3, label: '3%' },
                { value: 7, label: '7%' },
                { value: 10, label: '10%' },
                { value: 15, label: '15%' }
              ]}
              valueLabelDisplay="auto"
            />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>
              Position Sizing: {positionSizingPercentage}% of capital per trade
            </Typography>
            <Slider
              value={positionSizingPercentage}
              onChange={(e, value) => setPositionSizingPercentage(value as number)}
              min={1}
              max={20}
              step={0.5}
              marks={[
                { value: 1, label: '1%' },
                { value: 5, label: '5%' },
                { value: 10, label: '10%' },
                { value: 15, label: '15%' },
                { value: 20, label: '20%' }
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              Recommended: 1-5% for conservative, 5-10% for moderate, 10-20% for aggressive
            </Typography>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              onClick={handleUpdatePreferences}
              disabled={loading}
            >
              Save Preferences
            </Button>
          </Box>
        </TabPanel>

        {/* Column Preferences Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Trades Table Column Preferences
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Select which columns to display in the trades table. Click "Save Column Preferences" when done.
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
            {Object.entries(tradesColumns).map(([key, value]) => (
              <FormControlLabel
                key={key}
                control={
                  <Checkbox
                    checked={value}
                    onChange={(e) => {
                      const newColumns = { ...tradesColumns, [key]: e.target.checked };
                      setTradesColumns(newColumns);
                    }}
                  />
                }
                label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              />
            ))}
          </Box>
          
          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              onClick={() => {
                console.log('tradesColumns state:', tradesColumns);
                handleUpdatePreferences(tradesColumns);
              }}
              disabled={loading}
            >
              Save Column Preferences
            </Button>
          </Box>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserProfile;

