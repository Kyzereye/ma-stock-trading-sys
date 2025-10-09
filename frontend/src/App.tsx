import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, AppBar, Toolbar, Typography, Box, Tabs, Tab, IconButton } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import LogoutIcon from '@mui/icons-material/Logout';
import EMATrading from './components/EMATrading';
import MAOptimization from './components/MAOptimization';
import Login from './components/Login';
import Register from './components/Register';
import EmailVerification from './components/EmailVerification';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

const MainApp = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [showRegister, setShowRegister] = useState(false);
  const [showVerification, setShowVerification] = useState(false);

  // Check for email verification token in URL
  const urlParams = new URLSearchParams(window.location.search);
  const verificationToken = urlParams.get('token');

  // Set verification state on mount if token exists
  React.useEffect(() => {
    if (verificationToken && !isAuthenticated) {
      setShowVerification(true);
    }
  }, [verificationToken, isAuthenticated]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Show email verification if token is present
  if (showVerification && !isAuthenticated) {
    return (
      <EmailVerification 
        token={verificationToken || ''} 
        onComplete={() => {
          // Clear token from URL and go to login
          window.history.replaceState({}, document.title, window.location.pathname);
          setShowVerification(false);
          setShowRegister(false);
        }} 
      />
    );
  }

  if (!isAuthenticated) {
    return showRegister ? (
      <Register onSwitchToLogin={() => setShowRegister(false)} />
    ) : (
      <Login onSwitchToRegister={() => setShowRegister(true)} />
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <TrendingUpIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            MA Stock Trading System
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            Welcome, {user?.name}
          </Typography>
          <IconButton color="inherit" onClick={logout} title="Logout">
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered>
          <Tab label="Trading Analysis" />
          <Tab label="MA Optimization" />
        </Tabs>
      </Box>
      
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {tabValue === 0 && <EMATrading />}
        {tabValue === 1 && <MAOptimization />}
      </Container>
    </Box>
  );
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <MainApp />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;