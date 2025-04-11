import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Box, 
  Paper, 
  Typography, 
  LinearProgress, 
  Chip,
  Alert,
  useTheme
} from '@mui/material';
import {
  HourglassEmpty,
  PlayArrow,
  Pause,
  CheckCircle,
  Error as ErrorIcon,
  Analytics
} from '@mui/icons-material';

const ProgressTracker = ({ status, progress, error }) => {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const roundedProgress = Math.round(progress);
  
  // Determine status icon and color
  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return { icon: <HourglassEmpty />, color: 'default', label: t('conversion.status.pending') };
      case 'processing':
        return { icon: <PlayArrow />, color: 'primary', label: t('conversion.status.processing') };
      case 'paused':
        return { icon: <Pause />, color: 'secondary', label: t('conversion.status.paused') };
      case 'completed':
        return { icon: <CheckCircle />, color: 'success', label: t('conversion.status.completed') };
      case 'error':
        return { icon: <ErrorIcon />, color: 'error', label: t('conversion.status.error') };
      case 'analysis':
        return { icon: <Analytics />, color: 'info', label: t('progress.analysis') };
      default:
        return { icon: <HourglassEmpty />, color: 'default', label: status };
    }
  };
  
  const statusConfig = getStatusConfig();
  
  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 3, 
        mb: 3,
        borderRadius: 3,
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
      }}
    >
      <Typography 
        variant="h6" 
        gutterBottom
        sx={{ 
          fontWeight: 600,
          color: theme.palette.text.primary,
          mb: 2
        }}
      >
        {t('progress.title')}
      </Typography>
      
      <Box display="flex" alignItems="center" mb={2.5}>
        <Chip
          icon={statusConfig.icon}
          label={statusConfig.label}
          color={statusConfig.color}
          variant="filled"
          sx={{ 
            mr: 2, 
            fontWeight: 500,
            px: 1,
            '& .MuiChip-icon': {
              mr: 0.5
            }
          }}
        />
        <Typography 
          variant="body1" 
          sx={{ 
            fontWeight: 500,
            color: theme.palette.text.secondary,
            direction: i18n.language === 'he' ? 'rtl' : 'ltr'
          }}
        >
          {/* Direct numerical display without using translation variables */}
          {i18n.language === 'he' ? 
            `${t('progress.completed')} ${roundedProgress}%` : 
            `${roundedProgress}% ${t('progress.completed')}`
          }
        </Typography>
      </Box>
      
      <LinearProgress 
        variant={status === 'processing' || status === 'analysis' ? 'indeterminate' : 'determinate'} 
        value={roundedProgress}
        color={statusConfig.color !== 'default' ? statusConfig.color : 'primary'}
        sx={{ 
          height: 10, 
          borderRadius: 5, 
          mb: 2,
          '& .MuiLinearProgress-bar': {
            transition: 'transform 0.4s ease'
          },
          bgcolor: theme.palette.grey[200]
        }}
      />
      
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mt: 2,
            borderRadius: 2,
            '& .MuiAlert-icon': {
              alignItems: 'center'
            }
          }}
        >
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default ProgressTracker; 