import React, { useState, useEffect } from 'react';
import { Box, Button, TextField, Typography, Container, List, ListItem, Paper, IconButton, Slider } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { getMoods, createMood, deleteMood } from '../services/api';
import type { Mood } from '../services/api';

const MoodTracker: React.FC = () => {
  const [moodScore, setMoodScore] = useState<number>(5);
  const [moodLabel, setMoodLabel] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [moods, setMoods] = useState<Mood[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMoods();
  }, []);

  const fetchMoods = async () => {
    try {
      const data = await getMoods();
      setMoods(data);
    } catch (err) {
      setError('Failed to fetch mood entries');
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
    } catch (err) {
      setError('Failed to create mood entry');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMood = async (id: number) => {
    try {
      await deleteMood(id);
      setMoods(moods.filter(mood => mood.id !== id));
    } catch (error) {
      console.error('Error deleting mood:', error);
    }
  };

  const getMoodLabel = (score: number) => {
    if (score <= 2) return '😢 Sad';
    if (score <= 4) return '😕 Neutral';
    if (score <= 7) return '🙂 Good';
    return '😊 Great';
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Mood Tracker
      </Typography>

      <Box component="form" onSubmit={handleSubmit} sx={{ mb: 4 }}>
        <Typography gutterBottom>How are you feeling today?</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography sx={{ mr: 2 }}>😢</Typography>
          <Slider
            value={moodScore}
            onChange={(_, value) => setMoodScore(value as number)}
            min={1}
            max={10}
            step={1}
            marks
            sx={{ flexGrow: 1 }}
          />
          <Typography sx={{ ml: 2 }}>😊</Typography>
        </Box>

        <TextField
          fullWidth
          label="Mood Label"
          value={moodLabel}
          onChange={(e) => setMoodLabel(e.target.value)}
          margin="normal"
          required
        />

        <TextField
          fullWidth
          label="Notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          margin="normal"
          multiline
          rows={3}
        />

        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={loading}
          sx={{ mt: 2 }}
        >
          {loading ? 'Saving...' : 'Save Mood'}
        </Button>

        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
      </Box>

      <Typography variant="h5" gutterBottom>
        Recent Moods
      </Typography>

      <List>
        {moods.map((mood) => (
          <ListItem key={mood.id} divider>
            <Paper sx={{ p: 2, flexGrow: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="h6" gutterBottom>
                    {getMoodLabel(mood.mood_score)}
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 1 }}>
                    {mood.notes}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(mood.created_at).toLocaleString()}
                  </Typography>
                </Box>
                <IconButton 
                  onClick={() => handleDeleteMood(mood.id)}
                  color="error"
                  size="small"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </Paper>
          </ListItem>
        ))}
      </List>
    </Container>
  );
};

export default MoodTracker; 