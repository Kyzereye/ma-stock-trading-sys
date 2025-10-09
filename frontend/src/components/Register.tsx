import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Link as MuiLink,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import { useAuth } from '../contexts/AuthContext';
import EmailSentDialog from './shared/EmailSentDialog';

interface RegisterProps {
  onSwitchToLogin: () => void;
}

interface PasswordRequirements {
  minLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
  passwordsMatch: boolean;
}

const Register: React.FC<RegisterProps> = ({ onSwitchToLogin }) => {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [requirements, setRequirements] = useState<PasswordRequirements>({
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecial: false,
    passwordsMatch: false
  });

  useEffect(() => {
    // Update password requirements as user types
    // Passwords match only if both fields have content and they're equal
    const passwordsMatch = password.length > 0 && confirmPassword.length > 0 && password === confirmPassword;
    
    setRequirements({
      minLength: password.length >= 11,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password),
      passwordsMatch: passwordsMatch
    });
  }, [password, confirmPassword]);

  const isPasswordValid = () => {
    return Object.values(requirements).every(req => req === true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!isPasswordValid()) {
      setError('Password does not meet all requirements');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    const result = await register(email, password, name);

    if (result.success) {
      // Show success dialog instead of inline message
      setShowSuccessDialog(true);
      // Clear form
      setName('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
    } else {
      setError(result.error || 'Registration failed');
    }
    
    setLoading(false);
  };

  const handleCloseDialog = () => {
    setShowSuccessDialog(false);
    // Go directly to login page
    onSwitchToLogin();
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        bgcolor: 'background.default',
        py: 4
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          maxWidth: 500,
          width: '100%',
          mx: 2
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Create Account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            margin="normal"
            required
            autoFocus
          />

          <TextField
            fullWidth
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            required
          />

          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
          />

          <TextField
            fullWidth
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            margin="normal"
            required
          />

          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Password Requirements:
            </Typography>
            <List dense>
              <ListItem disablePadding>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {requirements.minLength ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText primary="At least 11 characters" />
              </ListItem>
              <ListItem disablePadding>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {requirements.hasUppercase ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText primary="At least one uppercase letter" />
              </ListItem>
              <ListItem disablePadding>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {requirements.hasLowercase ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText primary="At least one lowercase letter" />
              </ListItem>
              <ListItem disablePadding>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {requirements.hasNumber ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText primary="At least one number" />
              </ListItem>
              <ListItem disablePadding>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {requirements.hasSpecial ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText primary="At least one special character (!@#$%^&*...)" />
              </ListItem>
              <ListItem disablePadding>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {requirements.passwordsMatch ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText primary="Passwords match" />
              </ListItem>
            </List>
          </Box>

          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={loading || !isPasswordValid()}
            sx={{ mt: 2, mb: 2 }}
          >
            {loading ? 'Creating account...' : 'Register'}
          </Button>

          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Typography variant="body2">
              Already have an account?{' '}
              <MuiLink
                component="button"
                type="button"
                onClick={onSwitchToLogin}
                sx={{ cursor: 'pointer' }}
              >
                Login here
              </MuiLink>
            </Typography>
          </Box>
        </form>
      </Paper>

      {/* Email Sent Dialog */}
      <EmailSentDialog 
        open={showSuccessDialog}
        email={email}
        onClose={handleCloseDialog}
      />
    </Box>
  );
};

export default Register;

