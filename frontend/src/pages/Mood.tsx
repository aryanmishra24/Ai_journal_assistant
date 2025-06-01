import React, { useState, useEffect, useCallback } from 'react';
import { Box, Button, TextField, Typography, Container, List, ListItem, Paper, IconButton, Slider, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Alert } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { getMoods, createMood, deleteMood, generateMoodSummary } from '../services/api';
import type { Mood as MoodType, DailyMoodSummary } from '../services/api';
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
  const [summariesLoading, setSummariesLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [dailySummary, setDailySummary] = useState<DailyMoodSummary | null>(null);
  const [summaryCache, setSummaryCache] = useState<Record<string, DailyMoodSummary>>({});
  const [isGenerating, setIsGenerating] = useState(false);

  // Load cached summary when date changes
  useEffect(() => {
    if (selectedDate && summaryCache[selectedDate]) {
      setDailySummary(summaryCache[selectedDate]);
      // Keep the accordion expanded when switching dates if we have a cached summary
      setExpanded(true);
    } else {
      setDailySummary(null);
      setExpanded(false);
    }
    setIsGenerating(false);
  }, [selectedDate, summaryCache]);

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
  }, [fetchMoods]);

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
      fetchMoods();
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
    return entries.filter(mood => {
      const moodDate = new Date(mood.created_at);
      return moodDate.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        timeZone: 'Asia/Kolkata'
      }) === selectedDate;
    });
  };

  const generateSummary = async () => {
    if (isGenerating) return;
    
    try {
      setIsGenerating(true);
      setSummariesLoading(true);
      setSummaryError(null);

      console.log('=== Mood Summary Debug ===');
      console.log('Selected date:', selectedDate);
      console.log('Current entries:', entries.map(e => ({
        id: e.id,
        mood_score: e.mood_score,
        mood_label: e.mood_label,
        created_at: e.created_at,
        ist_date: new Date(e.created_at).toLocaleDateString('en-IN', {
          timeZone: 'Asia/Kolkata',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        })
      })));
      
      // Format date as YYYY-MM-DD if provided
      const formattedDate = selectedDate ? selectedDate.split('/').reverse().join('-') : null;
      console.log('Formatted date for API:', formattedDate);
      
      const response = await generateMoodSummary(formattedDate);
      console.log('Received summary response:', response);
      
      // Add timestamp to the summary for cache invalidation
      const summaryWithTimestamp = {
        ...response,
        timestamp: Date.now()
      };
      
      // Update cache and state
      if (selectedDate) {
        setSummaryCache(prev => ({
          ...prev,
          [selectedDate]: summaryWithTimestamp
        }));
      }
      setDailySummary(summaryWithTimestamp);
      // Keep the accordion expanded after generating summary
      setExpanded(true);
    } catch (err: any) {
      console.error('Error generating summary:', err);
      if (err.response?.status === 404) {
        setSummaryError(`No mood entries found for ${selectedDate || 'today'}. Please add some entries first.`);
      } else {
        setSummaryError('Unable to generate summary. Please try again.');
      }
      setExpanded(false);
    } finally {
      setSummariesLoading(false);
      setIsGenerating(false);
    }
  };

  const handleAccordionChange = async (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpanded(isExpanded);
    
    if (isExpanded) {
      // For any date (including today), first check if we have a cached summary
      if (selectedDate && summaryCache[selectedDate]) {
        setDailySummary(summaryCache[selectedDate]);
        return;
      }
      
      // If no cached summary, generate a new one
      await generateSummary();
    }
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
          onChange={handleAccordionChange}
          sx={{ 
            mb: 4, 
            bgcolor: 'rgba(121, 85, 58, 0.2)', 
            color: 'primary.contrastText',
            transition: 'all 0.2s ease-in-out',
            '&.Mui-expanded': {
              margin: '16px 0',
            }
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon sx={{ 
              color: 'primary.contrastText',
              transition: 'transform 0.2s ease-in-out',
              transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)'
            }} />}
            sx={{
              '& .MuiAccordionSummary-content': {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                transition: 'margin 0.2s ease-in-out',
              }
            }}
          >
            <Typography variant="h6">
              {selectedDate ? `Summary for ${selectedDate}` : 'Today\'s Summary'}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {summariesLoading ? (
              <Box 
                display="flex" 
                flexDirection="column"
                alignItems="center" 
                p={2}
                sx={{
                  animation: 'fadeIn 0.2s ease-in-out',
                  '@keyframes fadeIn': {
                    '0%': { opacity: 0 },
                    '100%': { opacity: 1 }
                  }
                }}
              >
                <CircularProgress color="inherit" />
                <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
                  Generating your daily mood summary...
                </Typography>
              </Box>
            ) : summaryError ? (
              <Alert 
                severity="info" 
                sx={{ 
                  mb: 2,
                  animation: 'slideIn 0.2s ease-in-out',
                  '@keyframes slideIn': {
                    '0%': { transform: 'translateY(-10px)', opacity: 0 },
                    '100%': { transform: 'translateY(0)', opacity: 1 }
                  }
                }}
              >
                {summaryError}
              </Alert>
            ) : dailySummary ? (
              <Box sx={{ 
                p: 2, 
                bgcolor: 'rgba(121, 85, 58, 0.2)', 
                borderRadius: 1,
                border: '1px solid rgba(121, 85, 58, 0.3)',
                animation: 'fadeIn 0.2s ease-in-out',
                '@keyframes fadeIn': {
                  '0%': { opacity: 0 },
                  '100%': { opacity: 1 }
                }
              }}>
                <Typography variant="h6" gutterBottom>
                  Mood Analysis
                </Typography>
                <Typography variant="body1" gutterBottom>
                  Average Mood: {dailySummary.average_mood.toFixed(1)}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  Mood Distribution:
                </Typography>
                <Box sx={{ mb: 2 }}>
                  {Object.entries(dailySummary.mood_distribution).map(([label, count]) => (
                    <Typography key={label} variant="body2">
                      {label}: {count} entries
                    </Typography>
                  ))}
                </Box>
                <Typography variant="h6" gutterBottom>
                  Summary
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                  {dailySummary.summary}
                </Typography>
              </Box>
            ) : (
              <Typography variant="body1">
                Click to expand and generate your daily mood summary
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
                  {new Date(mood.created_at).toLocaleString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                  })}
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