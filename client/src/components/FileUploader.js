import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDropzone } from 'react-dropzone';
import { 
  Box, 
  Paper, 
  Typography, 
  Button, 
  Alert, 
  CircularProgress 
} from '@mui/material';
import { UploadFile, CheckCircle, Error } from '@mui/icons-material';
import { uploadFile } from '../services/api';

const FileUploader = ({ onUploadSuccess }) => {
  const { t } = useTranslation();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  
  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive, acceptedFiles, fileRejections } = useDropzone({
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 10485760, // 10MB
    maxFiles: 1,
    disabled: uploading,
    onDropRejected: (fileRejections) => {
      const error = fileRejections[0]?.errors[0];
      if (error?.code === 'file-too-large') {
        setUploadError(t('error.fileSize'));
      } else if (error?.code === 'file-invalid-type') {
        setUploadError(t('error.invalidFile'));
      } else {
        setUploadError(t('error.generic'));
      }
    }
  });
  
  // Get the selected file
  const file = acceptedFiles[0];
  
  // Handle file upload
  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setUploadError(null);
    
    try {
      const response = await uploadFile(file);
      setUploadSuccess(true);
      onUploadSuccess(response);
    } catch (error) {
      setUploadError(error.message || t('error.upload'));
      setUploadSuccess(false);
    } finally {
      setUploading(false);
    }
  };
  
  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t('upload.title')}
      </Typography>
      
      <Box 
        {...getRootProps()} 
        className="dropzone"
        sx={{ 
          p: 3, 
          mb: 2, 
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          bgcolor: isDragActive ? 'primary.50' : 'background.paper',
          cursor: uploading ? 'not-allowed' : 'pointer'
        }}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <Box display="flex" flexDirection="column" alignItems="center">
            <CircularProgress size={40} sx={{ mb: 2 }} />
            <Typography>{t('uploading')}...</Typography>
          </Box>
        ) : (
          <Box display="flex" flexDirection="column" alignItems="center">
            <UploadFile fontSize="large" color="primary" sx={{ mb: 2 }} />
            <Typography>{t('upload.dropzone')}</Typography>
          </Box>
        )}
      </Box>
      
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
        {t('upload.limits')}
      </Typography>
      
      {file && !uploadSuccess && !uploading && (
        <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
          <Box flexGrow={1}>
            <Typography variant="body2" noWrap>
              {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </Typography>
          </Box>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleUpload} 
            disabled={uploading}
          >
            {t('upload.button')}
          </Button>
        </Box>
      )}
      
      {uploadError && (
        <Alert severity="error" icon={<Error />} sx={{ mb: 2 }}>
          {uploadError}
        </Alert>
      )}
      
      {uploadSuccess && (
        <Alert severity="success" icon={<CheckCircle />}>
          {t('upload.success')}
        </Alert>
      )}
    </Paper>
  );
};

export default FileUploader; 