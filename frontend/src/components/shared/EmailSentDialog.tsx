import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';

interface EmailSentDialogProps {
  open: boolean;
  email: string;
  onClose: () => void;
}

const EmailSentDialog: React.FC<EmailSentDialogProps> = ({ open, email, onClose }) => {
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
        <EmailIcon sx={{ fontSize: 60, color: 'success.main', mb: 1 }} />
        <Typography variant="h5">
          Check Your Email!
        </Typography>
      </DialogTitle>
      <DialogContent>
        <Typography variant="body1" paragraph>
          We've sent a verification email to <strong>{email}</strong>
        </Typography>
        <Typography variant="body2" paragraph color="text.secondary">
          Please follow these steps to complete your registration:
        </Typography>
        <List dense>
          <ListItem>
            <ListItemIcon sx={{ minWidth: 36 }}>
              <Typography variant="h6" color="primary">1</Typography>
            </ListItemIcon>
            <ListItemText 
              primary="Check your email inbox"
              secondary="Look for an email from MA Stock Trading"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon sx={{ minWidth: 36 }}>
              <Typography variant="h6" color="primary">2</Typography>
            </ListItemIcon>
            <ListItemText 
              primary="Click the verification link"
              secondary="This will activate your account"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon sx={{ minWidth: 36 }}>
              <Typography variant="h6" color="primary">3</Typography>
            </ListItemIcon>
            <ListItemText 
              primary="Return to login"
              secondary="Use your email and password to sign in"
            />
          </ListItem>
        </List>
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Note:</strong> The verification link will expire in 15 minutes. 
            If you don't see the email, check your spam folder.
          </Typography>
        </Alert>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button 
          onClick={onClose} 
          variant="contained" 
          fullWidth
        >
          Got it, take me to login
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default EmailSentDialog;

