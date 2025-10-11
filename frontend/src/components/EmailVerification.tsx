import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Button
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:2222';

interface EmailVerificationProps {
  token: string;
  onComplete: () => void;
}

const EmailVerification: React.FC<EmailVerificationProps> = ({ token, onComplete }) => {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const hasVerified = useRef(false);

  useEffect(() => {
    const verifyEmail = async () => {
      // Prevent double verification in React Strict Mode
      if (hasVerified.current) {
        return;
      }
      hasVerified.current = true;

      try {
        const response = await fetch(`${API_URL}/api/auth/verify-email/${token}`);
        const data = await response.json();

        if (data.success) {
          setStatus('success');
          setMessage(data.message);
        } else {
          setStatus('error');
          setMessage(data.error || 'Verification failed');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Failed to verify email. Please try again.');
      }
    };

    verifyEmail();
  }, [token]);

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        bgcolor: 'background.default'
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          maxWidth: 500,
          width: '100%',
          mx: 2,
          textAlign: 'center'
        }}
      >
        {status === 'loading' && (
          <>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h5" gutterBottom>
              Verifying your email...
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Please wait while we verify your account.
            </Typography>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircleIcon 
              sx={{ fontSize: 80, color: 'success.main', mb: 2 }} 
            />
            <Typography variant="h5" gutterBottom>
              Email Verified!
            </Typography>
            <Alert severity="success" sx={{ mt: 2, mb: 3 }}>
              {message}
            </Alert>
            <Button
              variant="contained"
              fullWidth
              onClick={onComplete}
            >
              Continue to Login
            </Button>
          </>
        )}

        {status === 'error' && (
          <>
            <ErrorIcon 
              sx={{ fontSize: 80, color: 'error.main', mb: 2 }} 
            />
            <Typography variant="h5" gutterBottom>
              Verification Failed
            </Typography>
            <Alert severity="error" sx={{ mt: 2, mb: 3 }}>
              {message}
            </Alert>
            <Button
              variant="contained"
              fullWidth
              onClick={onComplete}
            >
              Return to Login
            </Button>
          </>
        )}
      </Paper>
    </Box>
  );
};

export default EmailVerification;

