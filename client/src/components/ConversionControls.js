import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Box, 
  Paper, 
  Typography, 
  Button, 
  FormControl, 
  RadioGroup, 
  FormControlLabel, 
  Radio,
  ButtonGroup,
  Alert
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Replay,
  Cancel,
  Download
} from '@mui/icons-material';
import { 
  startConversion, 
  pauseConversion, 
  resumeConversion, 
  cancelConversion,
  getDownloadUrl
} from '../services/api';

const ConversionControls = ({ sessionId, status, onStatusChange, onFormatChange }) => {
  const { t } = useTranslation();
  const [outputFormat, setOutputFormat] = useState('xlsx');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Check if process is running
  const isProcessing = status === 'processing';
  // Check if process is paused
  const isPaused = status === 'paused';
  // Check if process is completed
  const isCompleted = status === 'completed';
  // Check if process is in error state
  const isError = status === 'error';
  // Check if process is pending (not started)
  const isPending = status === 'pending';
  
  // Handle format change
  const handleFormatChange = (event) => {
    const newFormat = event.target.value;
    setOutputFormat(newFormat);
    // Notify parent component of format change
    if (onFormatChange) {
      onFormatChange(newFormat);
    }
  };
  
  // Handle start conversion
  const handleStart = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await startConversion(sessionId, outputFormat);
      onStatusChange(response.status);
    } catch (error) {
      setError(error.message || t('error.conversion'));
    } finally {
      setLoading(false);
    }
  };
  
  // Handle pause conversion
  const handlePause = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await pauseConversion(sessionId);
      onStatusChange(response.status);
    } catch (error) {
      setError(error.message || t('error.conversion'));
    } finally {
      setLoading(false);
    }
  };
  
  // Handle resume conversion
  const handleResume = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await resumeConversion(sessionId);
      onStatusChange(response.status);
    } catch (error) {
      setError(error.message || t('error.conversion'));
    } finally {
      setLoading(false);
    }
  };
  
  // Handle cancel conversion
  const handleCancel = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await cancelConversion(sessionId);
      onStatusChange(response.status);
    } catch (error) {
      setError(error.message || t('error.conversion'));
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t('conversion.title')}
      </Typography>
      
      {isPending && (
        <Box mb={2}>
          <Typography variant="body2" gutterBottom>
            {t('conversion.format')}
          </Typography>
          <FormControl component="fieldset">
            <RadioGroup
              row
              name="output-format"
              value={outputFormat}
              onChange={handleFormatChange}
            >
              <FormControlLabel
                value="csv"
                control={<Radio />}
                label={t('conversion.csv')}
              />
              <FormControlLabel
                value="xlsx"
                control={<Radio />}
                label={t('conversion.excel')}
              />
            </RadioGroup>
          </FormControl>
        </Box>
      )}
      
      <Box sx={{ mb: 2 }}>
        <ButtonGroup variant="contained" disabled={loading}>
          {isPending && (
            <Button
              startIcon={<PlayArrow />}
              onClick={handleStart}
              color="primary"
            >
              {t('conversion.start')}
            </Button>
          )}
          
          {isProcessing && (
            <Button
              startIcon={<Pause />}
              onClick={handlePause}
              color="secondary"
            >
              {t('conversion.pause')}
            </Button>
          )}
          
          {isPaused && (
            <Button
              startIcon={<Replay />}
              onClick={handleResume}
              color="primary"
            >
              {t('conversion.resume')}
            </Button>
          )}
          
          {(isProcessing || isPaused) && (
            <Button
              startIcon={<Cancel />}
              onClick={handleCancel}
              color="error"
            >
              {t('conversion.cancel')}
            </Button>
          )}
        </ButtonGroup>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default ConversionControls; 