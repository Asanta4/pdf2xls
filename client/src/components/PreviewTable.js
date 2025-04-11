import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Box, 
  Paper, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Button,
  Collapse,
  Stack
} from '@mui/material';
import { TableChart, ExpandMore, ExpandLess, Refresh } from '@mui/icons-material';
import { resetPreviewData } from '../services/api';

const PreviewTable = ({ data, columns, sessionId, onPreviewReset }) => {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  
  const toggleExpand = () => {
    setExpanded(!expanded);
  };
  
  const handleResetPreview = async () => {
    try {
      await resetPreviewData(sessionId);
      if (onPreviewReset) {
        onPreviewReset();
      }
    } catch (error) {
      console.error('Error resetting preview:', error);
    }
  };
  
  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6" component="div">
          {t('preview.title')}
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            startIcon={<Refresh />}
            onClick={handleResetPreview}
            size="small"
            color="secondary"
          >
            {t('preview.returnToFirstPage')}
          </Button>
          <Button
            startIcon={expanded ? <ExpandLess /> : <ExpandMore />}
            onClick={toggleExpand}
            size="small"
          >
            {expanded ? t('preview.hidePreview') : t('preview.showPreview')}
          </Button>
        </Stack>
      </Box>
      
      <Collapse in={expanded}>
        {(!data || data.length === 0) ? (
          <Typography color="text.secondary" align="center" sx={{ py: 3 }}>
            {t('preview.noData')}
          </Typography>
        ) : (
          <TableContainer component={Box} sx={{ maxHeight: 400 }}>
            <Table stickyHeader size="small" className="preview-table">
              <TableHead>
                <TableRow>
                  {columns.map((column, index) => (
                    <TableCell key={index}>
                      {column}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((row, rowIndex) => (
                  <TableRow key={rowIndex}>
                    {columns.map((column, colIndex) => (
                      <TableCell key={`${rowIndex}-${colIndex}`}>
                        {row[column]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Collapse>
    </Paper>
  );
};

export default PreviewTable; 