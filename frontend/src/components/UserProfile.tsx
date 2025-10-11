import React, { useState } from 'react';
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
  InputAdornment
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

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
  const { user, token } = useAuth();
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

  const handleUpdatePreferences = async () => {
    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/auth/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          default_days: defaultDays,
          default_atr_period: defaultAtrPeriod,
          default_atr_multiplier: defaultAtrMultiplier,
          default_ma_type: defaultMaType,
          default_initial_capital: defaultInitialCapital
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: 'Preferences saved successfully!' });
        
        // Update user data in localStorage
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          userData.preferences = {
            default_days: defaultDays,
            default_atr_period: defaultAtrPeriod,
            default_atr_multiplier: defaultAtrMultiplier,
            default_ma_type: defaultMaType,
            default_initial_capital: defaultInitialCapital
          };
          localStorage.setItem('user', JSON.stringify(userData));
        }
        
        // Reload page to refresh context
        setTimeout(() => {
          window.location.reload();
        }, 500);
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
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserProfile;

