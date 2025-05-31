import React from 'react';
import { Box, Container } from '@mui/material';
import SharedSidebar from './SharedSidebar';
import { JournalEntry, Mood } from '../services/api';

interface LayoutProps {
  children: React.ReactNode;
  type: 'journal' | 'mood';
  entries: (JournalEntry | Mood)[];
  selectedDate: string | null;
  onDateSelect: (date: string | null) => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const SIDEBAR_WIDTH = 240;

const Layout: React.FC<LayoutProps> = ({
  children,
  type,
  entries,
  selectedDate,
  onDateSelect,
  sidebarOpen,
  onToggleSidebar
}) => {
  return (
    <Box sx={{ display: 'flex', minHeight: 'calc(100vh - 64px)', mt: '64px' }}>
      <SharedSidebar
        type={type}
        entries={entries}
        selectedDate={selectedDate}
        onDateSelect={onDateSelect}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={onToggleSidebar}
      />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          transition: theme => theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.easeInOut,
            duration: theme.transitions.duration.standard,
          }),
          marginLeft: sidebarOpen ? `${SIDEBAR_WIDTH}px` : 0,
        }}
      >
        <Container 
          maxWidth="lg" 
          sx={{ 
            py: 3,
            px: 2,
            transition: theme => theme.transitions.create(['margin', 'width'], {
              easing: theme.transitions.easing.easeInOut,
              duration: theme.transitions.duration.standard,
            }),
          }}
        >
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default Layout; 