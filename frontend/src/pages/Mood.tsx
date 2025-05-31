import React, { useState, useEffect, useCallback } from 'react';
import { Box, Button, TextField, Typography, Container, List, ListItem, Paper, IconButton, Slider, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Alert } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { getMoods, createMood, deleteMood, getMoodStats, generateMoodSummary } from '../services/api';
import type { Mood as MoodType, MoodStats } from '../services/api';
import Layout from '../components/Layout';

interface MoodProps {
  selectedDate: string | null;
  onDateSelect: (date: string | null) => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  entries: MoodType[];
  setEntries: React.Dispatch<React.SetStateAction<MoodType[]>>;
}

const Mood: React.FC<MoodProps> = ({ 
  selectedDate, 
  onDateSelect,
  sidebarOpen,
  onToggleSidebar,
  entries,
  setEntries
}) => {
  const [moodScore, setMoodScore] = useState<number>(5);
  const [moodLabel, setMoodLabel] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moodStats, setMoodStats] = useState<MoodStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [summariesLoading, setSummariesLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchMoods = useCallback(async () => {
    try {
      const data = await getMoods();
      setEntries(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch mood entries');
    }
  }, [setEntries]);

  useEffect(() => {
    fetchMoods();
    fetchMoodStats();
  }, [fetchMoods]);

  const fetchMoodStats = async () => {
    try {
      setStatsLoading(true);
      const data = await getMoodStats(1);
      setMoodStats(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch mood statistics');
    } finally {
      setStatsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await createMood(moodScore, moodLabel, notes);
      setMoodScore(5);
      setMoodLabel('');
      setNotes('');
      fetchMoods();
      fetchMoodStats();
    } catch (err) {
      setError('Failed to create mood entry');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMood = async (id: number) => {
    try {
      await deleteMood(id);
      setEntries(entries.filter(mood => mood.id !== id));
      fetchMoodStats();
      setError(null);
    } catch (error) {
      setError('Failed to delete mood entry');
    }
  };

  const getMoodEmoji = (score: number) => {
    if (score <= 2) return '😢';
    if (score <= 4) return '😕';
    if (score <= 7) return '🙂';
    return '😊';
  };

  const getSelectedDateMoods = () => {
    if (!selectedDate) return entries;
    return entries.filter(mood => 
      new Date(mood.created_at).toLocaleDateString() === selectedDate
    );
  };

  return (
    <Layout
      type="mood"
      entries={entries}
      selectedDate={selectedDate}
      onDateSelect={onDateSelect}
      sidebarOpen={sidebarOpen}
      onToggleSidebar={onToggleSidebar}
    >
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom>
          {selectedDate ? `Mood - ${selectedDate}` : 'Today\'s Mood'}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Daily Mood Summary Section */}
        <Accordion 
          expanded={expanded}
          onChange={async (_, isExpanded) => {
            if (isExpanded && !moodStats?.summary && !summariesLoading) {
              try {
                setSummariesLoading(true);
                setSummaryError(null);
                console.log('Generating mood summary...');
                const response = await generateMoodSummary();
                console.log('Received summary response:', response);
                setMoodStats(prev => {
                  console.log('Previous moodStats:', prev);
                  const updated = prev ? {
                    ...prev,
                    summary: response.summary
                  } : null;
                  console.log('Updated moodStats:', updated);
                  return updated;
                });
              } catch (err: any) {
                console.error('Error generating summary:', err);
                if (err.response?.status === 404) {
                  setSummaryError('No mood entries found for today. Please add some mood entries first.');
                } else {
                  setSummaryError('Unable to generate summary. Please try again.');
                }
                setExpanded(false);
              } finally {
                setSummariesLoading(false);
              }
            } else {
              setExpanded(isExpanded);
            }
          }}
          sx={{ mb: 4, bgcolor: 'rgba(121, 85, 58, 0.2)', color: 'primary.contrastText' }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon sx={{ color: 'primary.contrastText' }} />}
            sx={{
              '& .MuiAccordionSummary-content': {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }
            }}
          >
            <Typography variant="h6">Today's Mood Summary</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {statsLoading || summariesLoading ? (
              <Box display="flex" justifyContent="center" p={2}>
                <CircularProgress color="inherit" />
              </Box>
            ) : summaryError ? (
              <Alert severity="info" sx={{ mb: 2 }}>
                {summaryError}
              </Alert>
            ) : moodStats ? (
              <Box>
                <Typography variant="body1" gutterBottom>
                  Average Mood: {getMoodEmoji(Math.round(moodStats.average_mood))} {moodStats.average_mood.toFixed(1)}/10
                </Typography>
                <Typography variant="body1" gutterBottom>
                  Mood Distribution:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
                  {Object.entries(moodStats.mood_distribution).map(([label, count]) => (
                    <Typography key={label} component="span" sx={{ 
                      bgcolor: 'rgba(255, 255, 255, 0.2)',
                      px: 1,
                      py: 0.5,
                      borderRadius: 1
                    }}>
                      {label}: {count}
                    </Typography>
                  ))}
                </Box>
                {moodStats.summary && (
                  <Box sx={{ 
                    mt: 2, 
                    p: 2, 
                    bgcolor: 'rgba(121, 85, 58, 0.2)', 
                    borderRadius: 1,
                    border: '1px solid rgba(121, 85, 58, 0.3)'
                  }}>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                      {moodStats.summary}
                    </Typography>
                  </Box>
                )}
              </Box>
            ) : (
              <Typography variant="body1">
                Click to expand and generate your mood summary
              </Typography>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Mood Entry Form */}
        {!selectedDate && (
          <Paper sx={{ p: 3, mb: 4 }}>
            <form onSubmit={handleSubmit}>
              <Typography variant="h6" gutterBottom>
                How are you feeling?
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>
                  Mood Score: {moodScore}/10 {getMoodEmoji(moodScore)}
                </Typography>
                <Slider
                  value={moodScore}
                  onChange={(_, value) => setMoodScore(value as number)}
                  min={1}
                  max={10}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <TextField
                fullWidth
                label="Mood Label"
                value={moodLabel}
                onChange={(e) => setMoodLabel(e.target.value)}
                sx={{ mb: 2 }}
                required
              />

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                sx={{ mb: 2 }}
              />

              <Button
                type="submit"
                variant="contained"
                disabled={loading || !moodLabel.trim()}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Mood'}
              </Button>
            </form>
          </Paper>
        )}

        {/* Mood Entries */}
        <Typography variant="h5" gutterBottom>
          {selectedDate ? `Moods for ${selectedDate}` : 'Recent Moods'}
        </Typography>

        <List>
          {getSelectedDateMoods().map((mood) => (
            <ListItem key={mood.id} sx={{ display: 'block', mb: 2 }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography variant="h6">
                      {getMoodEmoji(mood.mood_score)} {mood.mood_score}/10
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                      {mood.mood_label}
                    </Typography>
                    {mood.notes && (
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {mood.notes}
                      </Typography>
                    )}
                  </Box>
                  {!selectedDate && (
                    <IconButton 
                      onClick={() => handleDeleteMood(mood.id)}
                      color="error"
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {new Date(mood.created_at).toLocaleString()}
                </Typography>
              </Paper>
            </ListItem>
          ))}
        </List>
      </Container>
    </Layout>
  );
};

export default Mood; 