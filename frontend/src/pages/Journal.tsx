import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  const [summaryCache, setSummaryCache] = useState<Record<string, DailySummary>>({});
  const [lastEntryUpdate, setLastEntryUpdate] = useState<Record<string, number>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update lastEntryUpdate when entries change
  useEffect(() => {
    const newLastEntryUpdate: Record<string, number> = {};
    entries.forEach(entry => {
      const entryDate = new Date(entry.created_at).toLocaleDateString('en-IN', {
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
      newLastEntryUpdate[entryDate] = Date.now();
    });
    setLastEntryUpdate(newLastEntryUpdate);
  }, [entries]);

  // Check if summary needs to be regenerated
  const shouldRegenerateSummary = (date: string | null) => {
    if (!date) return true;
    const lastUpdate = lastEntryUpdate[date];
    const cachedSummary = summaryCache[date];
    return !cachedSummary || !lastUpdate || lastUpdate > (cachedSummary as any).timestamp;
  };

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
      setError(null);
      
      // Get AI response first
      const aiResponse = await getAIResponse(newEntry);
      console.log('AI Response:', aiResponse); // Debug log
      
      // Create entry with AI response
      const entry = await createJournalEntry(newEntry, aiResponse.response);
      console.log('Created Entry:', entry); // Debug log
      
      // Update entries list with the new entry
      setEntries(prevEntries => [entry, ...prevEntries]);
      
      // Clear the input
      setNewEntry('');
      
      // If we're on a specific date view, refresh entries
      if (selectedDate) {
        fetchEntries();
      }
    } catch (error) {
      console.error('Error adding entry:', error);
      setError('Failed to add entry. Please try again.');
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
    return entries.filter(entry => {
      const entryDate = new Date(entry.created_at);
      return entryDate.toLocaleDateString('en-IN', {
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

      console.log('=== Journal Summary Debug ===');
      console.log('Selected date:', selectedDate);
      console.log('Current entries:', entries.map(e => ({
        id: e.id,
        content: e.content,
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
      
      const response = await generateDailySummary(formattedDate);
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
        setSummaryError(`No journal entries found for ${selectedDate || 'today'}. Please add some entries first.`);
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
                  Generating your daily summary...
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
                  {new Date(entry.created_at).toLocaleString('en-IN', {
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

export default Journal; 