import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  CssBaseline, 
  Container, 
  Box, 
  Typography, 
  AppBar, 
  Toolbar, 
  IconButton, 
  Menu, 
  MenuItem, 
  Button,
  Paper,
  useMediaQuery,
  Fade,
  Divider,
  Tooltip
} from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { 
  LanguageRounded, 
  ArrowBack, 
  CloudDownload, 
  Description, 
  TableChart
} from '@mui/icons-material';
import FileUploader from './components/FileUploader';
import ConversionControls from './components/ConversionControls';
import ProgressTracker from './components/ProgressTracker';
import { getSessionProgress, getDownloadUrl } from './services/api';

function App() {
  const { t, i18n } = useTranslation();
  const [session, setSession] = useState(null);
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [languageMenu, setLanguageMenu] = useState(null);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFormat, setSelectedFormat] = useState('xlsx'); // Track selected format
  
  // Check if on mobile screen
  const isMobile = useMediaQuery('(max-width:600px)');

  // Create theme based on language direction
  const theme = createTheme({
    direction: i18n.language === 'he' ? 'rtl' : 'ltr',
    palette: {
      mode: 'light',
      primary: {
        main: '#1976d2',
        light: '#42a5f5',
        dark: '#1565c0',
        contrastText: '#fff'
      },
      secondary: {
        main: '#e91e63',
        light: '#ec407a',
        dark: '#c2185b',
        contrastText: '#fff'
      },
      success: {
        main: '#2e7d32',
        light: '#4caf50',
        dark: '#1b5e20',
        contrastText: '#fff'
      },
      info: {
        main: '#0288d1',
        light: '#03a9f4',
        dark: '#01579b',
        contrastText: '#fff'
      },
      background: {
        default: '#f5f9ff',
        paper: '#ffffff'
      },
      grey: {
        50: '#fafafa',
        100: '#f5f5f5',
        200: '#eeeeee',
        300: '#e0e0e0',
        400: '#bdbdbd',
        500: '#9e9e9e',
        600: '#757575',
        700: '#616161',
        800: '#424242',
        900: '#212121',
      },
    },
    typography: {
      fontFamily: i18n.language === 'he' 
        ? "'Assistant', 'Rubik', 'Arial', sans-serif"
        : "'Roboto', 'Segoe UI', 'Arial', sans-serif",
      h4: {
        fontWeight: 700,
      },
      h5: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 600,
      },
      button: {
        textTransform: 'none',
        fontWeight: 500,
        fontSize: '0.9375rem',
      }
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            padding: '10px 20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            transition: 'all 0.2s ease'
          },
          containedPrimary: {
            '&:hover': {
              boxShadow: '0 4px 12px rgba(33,150,243,0.3)',
              transform: 'translateY(-2px)'
            }
          },
          containedSuccess: {
            '&:hover': {
              boxShadow: '0 4px 12px rgba(76,175,80,0.3)',
              transform: 'translateY(-2px)'
            }
          },
          outlined: {
            borderWidth: '1.5px',
            '&:hover': {
              borderWidth: '1.5px',
            }
          }
        }
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
          },
          elevation3: {
            boxShadow: '0 6px 25px rgba(0,0,0,0.07)'
          }
        }
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }
        }
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            margin: '16px 0'
          }
        }
      }
    }
  });

  // Handle language menu
  const handleLanguageMenuOpen = (event) => {
    setLanguageMenu(event.currentTarget);
  };

  const handleLanguageMenuClose = () => {
    setLanguageMenu(null);
  };

  const changeLanguage = (language) => {
    i18n.changeLanguage(language);
    handleLanguageMenuClose();
  };

  // Handle session updates
  const handleSessionCreated = (sessionData) => {
    setSession(sessionData);
    setStatus(sessionData.status);
    setProgress(0);
    setPolling(true);
  };

  // Handle status updates
  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    
    // If the status is completed or error, stop polling
    if (newStatus === 'completed' || newStatus === 'error') {
      setPolling(false);
    } else {
      setPolling(true);
    }
  };

  // Reset to file selection
  const handleReturnToFileSelection = () => {
    setSession(null);
    setStatus('pending');
    setProgress(0);
    setError(null);
    setPolling(false);
  };

  // Handle format selection
  const handleFormatChange = (format) => {
    setSelectedFormat(format);
  };

  // Handle download
  const handleDownload = () => {
    if (!session) return;
    
    const downloadUrl = getDownloadUrl(session.session_id, selectedFormat);
    window.open(downloadUrl, '_blank');
  };

  // Poll for progress updates
  useEffect(() => {
    let interval;
    
    if (polling && session) {
      interval = setInterval(async () => {
        try {
          const response = await getSessionProgress(session.session_id);
          
          setStatus(response.status);
          setProgress(response.progress);
          
          // Stop polling if completed or error
          if (response.status === 'completed' || response.status === 'error') {
            setPolling(false);
            if (response.error) {
              setError(response.error);
            }
          }
        } catch (error) {
          console.error('Error fetching progress:', error);
        }
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [polling, session]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        minHeight: '100vh', 
        bgcolor: 'background.default'
      }}>
        <AppBar position="static" elevation={0} color="primary">
          <Toolbar>
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                flexGrow: 1, 
                fontWeight: 600,
                fontSize: isMobile ? '1rem' : '1.25rem',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <TableChart fontSize="small" />
              {t('app.title')}
            </Typography>
            <Tooltip title={t('language.switch')} arrow>
              <IconButton
                color="inherit"
                onClick={handleLanguageMenuOpen}
                aria-controls="language-menu"
                aria-haspopup="true"
                sx={{ ml: 1 }}
                size="small"
              >
                <LanguageRounded />
              </IconButton>
            </Tooltip>
            <Menu
              id="language-menu"
              anchorEl={languageMenu}
              open={Boolean(languageMenu)}
              onClose={handleLanguageMenuClose}
              PaperProps={{
                elevation: 3,
                sx: {
                  borderRadius: 2,
                  mt: 1
                }
              }}
              TransitionComponent={Fade}
            >
              <MenuItem onClick={() => changeLanguage('he')}>{t('language.he')}</MenuItem>
              <MenuItem onClick={() => changeLanguage('en')}>{t('language.en')}</MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>
        
        <Container maxWidth="md" sx={{ mt: 4, mb: 4, flexGrow: 1, px: isMobile ? 2 : 3 }}>
          <Paper 
            elevation={0}
            sx={{ 
              py: 4, 
              px: isMobile ? 2 : 4, 
              textAlign: 'center',
              mb: 4,
              backgroundImage: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
              color: 'white',
              borderRadius: '16px',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {/* Decorative element */}
            <Box 
              sx={{
                position: 'absolute',
                top: -30,
                right: -30,
                width: 150,
                height: 150,
                borderRadius: '50%',
                backgroundColor: 'rgba(255,255,255,0.1)',
                zIndex: 1
              }}
            />
            
            <Box sx={{ position: 'relative', zIndex: 2 }}>
              <Typography 
                variant="h4" 
                component="h1" 
                gutterBottom
                sx={{ 
                  fontWeight: 700,
                  fontSize: isMobile ? '1.75rem' : '2.25rem',
                }}
              >
                {t('app.title')}
              </Typography>
              <Typography 
                variant="subtitle1" 
                sx={{ 
                  opacity: 0.9,
                  maxWidth: '600px',
                  mx: 'auto',
                  fontSize: isMobile ? '0.9rem' : '1rem',
                  mb: 2
                }}
              >
                {t('app.description')}
              </Typography>
            </Box>
          </Paper>
          
          <Paper
            elevation={3}
            sx={{ 
              p: isMobile ? 3 : 4,
              mb: 4,
              borderRadius: 3
            }}
          >
            {!session ? (
              <FileUploader onUploadSuccess={handleSessionCreated} />
            ) : (
              <>
                <ProgressTracker 
                  status={status} 
                  progress={progress} 
                  error={error}
                />
                
                <Box mt={3}>
                  <ConversionControls 
                    sessionId={session.session_id}
                    status={status}
                    onStatusChange={handleStatusChange}
                    onFormatChange={handleFormatChange}
                  />
                </Box>
                
                {status === 'completed' && (
                  <Fade in={status === 'completed'} timeout={500}>
                    <Box>
                      <Divider sx={{ my: 3 }} />
                      
                      <Typography variant="h5" gutterBottom align="center" sx={{ fontWeight: 600 }}>
                        {t('download.title')}
                      </Typography>
                      
                      <Typography 
                        variant="body1" 
                        align="center" 
                        color="text.secondary" 
                        paragraph
                        sx={{ maxWidth: '500px', mx: 'auto', mb: 3 }}
                      >
                        {t('download.description')}
                      </Typography>
                      
                      <Box 
                        sx={{ 
                          display: 'flex',
                          justifyContent: 'center',
                          my: 2
                        }}
                      >
                        {/* Show a single download button based on selected format */}
                        <Button
                          variant="contained"
                          color={selectedFormat === 'csv' ? 'primary' : 'success'}
                          startIcon={selectedFormat === 'csv' ? <Description /> : <CloudDownload />}
                          size="large"
                          onClick={handleDownload}
                          sx={{
                            minWidth: isMobile ? '100%' : '220px',
                            py: 1.5,
                            fontWeight: 600
                          }}
                        >
                          {selectedFormat === 'csv' 
                            ? t('controls.downloadCSV') 
                            : t('controls.downloadExcel')}
                        </Button>
                      </Box>
                      
                      <Box sx={{ textAlign: 'center', mt: 4 }}>
                        <Button
                          variant="outlined"
                          color="primary"
                          startIcon={<ArrowBack />}
                          onClick={handleReturnToFileSelection}
                          size="medium"
                        >
                          {t('controls.chooseAnotherFile')}
                        </Button>
                      </Box>
                    </Box>
                  </Fade>
                )}
              </>
            )}
          </Paper>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App; 