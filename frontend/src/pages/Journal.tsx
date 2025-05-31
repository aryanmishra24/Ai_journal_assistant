import React, { useState, useEffect, useCallback } from 'react';
import { Box, Button, TextField, Typography, Container, List, ListItem, Paper, CircularProgress, IconButton, Accordion, AccordionSummary, AccordionDetails, Alert } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { getJournalEntries, createJournalEntry, getAIResponse, generateDailySummary, deleteJournalEntry } from '../services/api';
import type { JournalEntry, DailySummary } from '../services/api';
import Layout from '../components/Layout';

interface JournalProps {
  selectedDate: string | null;
  onDateSelect: (date: string | null) => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  entries: JournalEntry[];
  setEntries: React.Dispatch<React.SetStateAction<JournalEntry[]>>;
}

const Journal: React.FC<JournalProps> = ({ 
  selectedDate, 
  onDateSelect,
  sidebarOpen,
  onToggleSidebar,
  entries,
  setEntries
}) => {
  const [newEntry, setNewEntry] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [summariesLoading, setSummariesLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);

  const fetchEntries = useCallback(async () => {
    try {
      const data = await getJournalEntries();
      setEntries(data);
    } catch (error) {
      console.error('Error fetching entries:', error);
    }
  }, [setEntries]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const handleAddEntry = async () => {
    if (!newEntry.trim()) return;

    try {
      setLoading(true);
      setAiLoading(true);
      
      const aiResponse = await getAIResponse(newEntry);
      const entry = await createJournalEntry(newEntry, aiResponse.response);
      
      setEntries([entry, ...entries]);
      setNewEntry('');
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
    } catch (error) {
      console.error('Error deleting entry:', error);
    }
  };

  const getSelectedDateEntries = () => {
    if (!selectedDate) return entries;
    return entries.filter(entry => 
      new Date(entry.created_at).toLocaleDateString() === selectedDate
    );
  };

  return (
    <Layout
      type="journal"
      entries={entries}
      selectedDate={selectedDate}
      onDateSelect={onDateSelect}
      sidebarOpen={sidebarOpen}
      onToggleSidebar={onToggleSidebar}
    >
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom>
          {selectedDate ? `Journal - ${selectedDate}` : 'Today\'s Journal'}
        </Typography>

        {/* Daily Summary Section */}
        <Accordion 
          expanded={expanded}
          onChange={async (_, isExpanded) => {
            if (isExpanded && !dailySummary && !summariesLoading) {
              try {
                setSummariesLoading(true);
                setSummaryError(null);
                console.log('Generating daily summary...');
                const response = await generateDailySummary();
                console.log('Received summary response:', response);
                setDailySummary(response);
              } catch (err: any) {
                console.error('Error generating summary:', err);
                if (err.response?.status === 404) {
                  setSummaryError('No journal entries found for today. Please add some entries first.');
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
            <Typography variant="h6">Today's Summary</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {summariesLoading ? (
              <Box display="flex" justifyContent="center" p={2}>
                <CircularProgress color="inherit" />
              </Box>
            ) : summaryError ? (
              <Alert severity="info" sx={{ mb: 2 }}>
                {summaryError}
              </Alert>
            ) : dailySummary ? (
              <Box sx={{ 
                p: 2, 
                bgcolor: 'rgba(121, 85, 58, 0.2)', 
                borderRadius: 1,
                border: '1px solid rgba(121, 85, 58, 0.3)'
              }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                  {dailySummary.summary}
                </Typography>
              </Box>
            ) : (
              <Typography variant="body1">
                Click to expand and generate your daily summary
              </Typography>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Journal Entry Form */}
        {!selectedDate && (
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
        )}

        {/* Entries */}
        <Typography variant="h5" gutterBottom>
          {selectedDate ? `Entries for ${selectedDate}` : 'Recent Entries'}
        </Typography>

        <List>
          {getSelectedDateEntries().map((entry) => (
            <ListItem key={entry.id} sx={{ display: 'block', mb: 2 }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Typography variant="body1" sx={{ mb: 2, flex: 1 }}>
                    {entry.content}
                  </Typography>
                  {!selectedDate && (
                    <IconButton 
                      onClick={() => handleDeleteEntry(entry.id)}
                      color="error"
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  )}
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
      </Container>
    </Layout>
  );
};

export default Journal; 