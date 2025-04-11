import axios from 'axios';

// Base URL for API requests
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8003';  // Use environment variable if available

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Timeout after 10 seconds
  timeout: 10000, 
});

// Upload a PDF file
export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    console.log('Uploading file to:', `${API_BASE_URL}/upload`);
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Upload file error:', error);
    handleApiError(error);
  }
};

// Start conversion
export const startConversion = async (sessionId, outputFormat) => {
  const formData = new FormData();
  formData.append('output_format', outputFormat);
  
  try {
    const response = await api.post(`/start/${sessionId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Pause conversion
export const pauseConversion = async (sessionId) => {
  try {
    const response = await api.post(`/pause/${sessionId}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Resume conversion
export const resumeConversion = async (sessionId) => {
  try {
    const response = await api.post(`/resume/${sessionId}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Cancel conversion
export const cancelConversion = async (sessionId) => {
  try {
    const response = await api.post(`/cancel/${sessionId}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Get conversion progress
export const getSessionProgress = async (sessionId) => {
  try {
    const response = await api.get(`/progress/${sessionId}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Get preview data
export const getPreviewData = async (sessionId) => {
  try {
    const response = await api.get(`/preview/${sessionId}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Get download URL
export const getDownloadUrl = (sessionId) => {
  return `${API_BASE_URL}/download/${sessionId}`;
};

// Reset preview data
export const resetPreviewData = async (sessionId) => {
  try {
    const response = await api.post(`/reset-preview/${sessionId}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Error handling helper
const handleApiError = (error) => {
  console.error('API Error:', error);
  
  if (error.response) {
    // Server responded with an error status
    console.error('Error response data:', error.response.data);
    console.error('Error response status:', error.response.status);
    const errorMessage = error.response.data.detail || 'An error occurred';
    throw new Error(errorMessage);
  } else if (error.request) {
    // Request was made but no response received
    console.error('No response received:', error.request);
    throw new Error('No response from server. Please check your connection.');
  } else {
    // Error setting up the request
    throw error;
  }
}; 