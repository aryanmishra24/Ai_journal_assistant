import React, { useState, useEffect } from 'react';
import { Box, Typography, Container, Paper, CircularProgress, Alert } from '@mui/material';
import { getJournalInsights } from '../services/api';

const Insights: React.FC = () => {
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const data = await getJournalInsights();
        setInsights(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch insights');
        setLoading(false);
      }
    };

    fetchInsights();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Journal Insights
      </Typography>
      
      {insights && (
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Writing Statistics
            </Typography>
            <Typography>Total Entries: {insights.stats.total_entries}</Typography>
            <Typography>Average Entry Length: {insights.stats.average_entry_length} words</Typography>
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Analysis
            </Typography>
            <Typography>Overall Sentiment: {insights.sentiment.overall_sentiment.toFixed(2)}</Typography>
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Top Keywords
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {insights.top_keywords.map((keyword: string, index: number) => (
                <Typography key={index} component="span" sx={{ 
                  bgcolor: 'primary.light', 
                  color: 'primary.contrastText',
                  px: 1,
                  py: 0.5,
                  borderRadius: 1
                }}>
                  {keyword}
                </Typography>
              ))}
            </Box>
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recommendations
            </Typography>
            <Box component="ul" sx={{ pl: 2 }}>
              {insights.recommendations.map((rec: string, index: number) => (
                <Typography key={index} component="li" sx={{ mb: 1 }}>
                  {rec}
                </Typography>
              ))}
            </Box>
          </Paper>
        </>
      )}
    </Container>
  );
};

export default Insights; 