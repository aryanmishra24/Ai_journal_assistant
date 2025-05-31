import React, { useState, useEffect } from 'react';
import { Box, Button, TextField, Typography, Container, List, ListItem, Paper, CircularProgress, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { getJournalEntries, createJournalEntry, getAIResponse, getDailySummary, generateDailySummary, deleteJournalEntry } from '../services/api';

const Journal: React.FC = () => {
  const [entries, setEntries] = useState<any[]>([]);
  const [newEntry, setNewEntry] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [dailySummary, setDailySummary] = useState<string | null>(null);

  useEffect(() => {
    fetchEntries();
    fetchDailySummary();
  }, []);

  const fetchEntries = async () => {
    try {
      const data = await getJournalEntries();
      setEntries(data);
    } catch (error) {
      console.error('Error fetching entries:', error);
    }
  };

  const fetchDailySummary = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      try {
        const data = await getDailySummary(today);
        setDailySummary(data.summary);
      } catch (error) {
        // If summary doesn't exist, generate one
        const generatedSummary = await generateDailySummary();
        setDailySummary(generatedSummary.summary);
      }
    } catch (error) {
      console.error('Error fetching/generating daily summary:', error);
    }
  };

  const handleAddEntry = async () => {
    if (!newEntry.trim()) return;

    try {
      setLoading(true);
      setAiLoading(true);
      
      // Get AI response first
      const aiResponse = await getAIResponse(newEntry);
      
      // Create journal entry with AI response
      const entry = await createJournalEntry(newEntry, aiResponse.response);
      
      // Update entries list
      setEntries([entry, ...entries]);
      setNewEntry('');
      
      // Refresh daily summary
      fetchDailySummary();
    } catch (error) {
      console.error('Error adding entry:', error);
    } finally {
      setLoading(false);
      setAiLoading(false);
    }
  };

  const handleDeleteEntry = async (id: number) => {
    try {
      await deleteJournalEntry(id);
      setEntries(entries.filter(entry => entry.id !== id));
      // Refresh summary after deleting an entry
      fetchDailySummary();
    } catch (error) {
      console.error('Error deleting entry:', error);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Journal
        </Typography>

        {dailySummary && (
          <Paper sx={{ p: 2, mb: 3, bgcolor: '#f5f5f5' }}>
            <Typography variant="h6" gutterBottom>
              Today's Summary
            </Typography>
            <Typography>{dailySummary}</Typography>
          </Paper>
        )}

        <Box sx={{ mb: 4 }}>
          <TextField
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            label="What's on your mind?"
            value={newEntry}
            onChange={(e) => setNewEntry(e.target.value)}
            sx={{ mb: 2 }}
            disabled={loading}
          />
          <Button
            variant="contained"
            onClick={handleAddEntry}
            disabled={loading || !newEntry.trim()}
          >
            {loading ? <CircularProgress size={24} /> : 'Add Entry'}
          </Button>
          {aiLoading && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Getting AI response...
            </Typography>
          )}
        </Box>

        <List>
          {entries.map((entry) => (
            <ListItem key={entry.id} sx={{ display: 'block', mb: 2 }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Typography variant="body1" sx={{ mb: 2, flex: 1 }}>
                    {entry.content}
                  </Typography>
                  <IconButton 
                    onClick={() => handleDeleteEntry(entry.id)}
                    color="error"
                    size="small"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
                {entry.ai_response && (
                  <Box sx={{ mt: 2, pl: 2, borderLeft: '2px solid #e0e0e0' }}>
                    <Typography variant="body2" color="text.secondary">
                      AI Response:
                    </Typography>
                    <Typography variant="body2">
                      {entry.ai_response}
                    </Typography>
                  </Box>
                )}
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {new Date(entry.created_at).toLocaleString()}
                </Typography>
              </Paper>
            </ListItem>
          ))}
        </List>
      </Box>
    </Container>
  );
};

export default Journal; 