import React, { useEffect, useRef } from 'react';
import { Drawer, List, ListItemButton, ListItemText, IconButton, useTheme } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { JournalEntry, Mood } from '../services/api';

interface SharedSidebarProps {
  selectedDate: string | null;
  onDateSelect: (date: string | null) => void;
  entries: (JournalEntry | Mood)[];
  type: 'journal' | 'mood';
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const SIDEBAR_WIDTH = 240;

const SharedSidebar: React.FC<SharedSidebarProps> = ({
  selectedDate,
  onDateSelect,
  entries,
  type,
  sidebarOpen,
  onToggleSidebar
}) => {
  const theme = useTheme();
  const sidebarRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const isTransitioning = useRef(false);
  const lastClickTime = useRef(0);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const now = Date.now();
      if (isTransitioning.current || now - lastClickTime.current < 300) return;
      
      const target = event.target as Node;
      const isClickInsideSidebar = sidebarRef.current?.contains(target);
      const isClickOnToggle = toggleRef.current?.contains(target);

      if (sidebarOpen && !isClickInsideSidebar && !isClickOnToggle) {
        lastClickTime.current = now;
        isTransitioning.current = true;
        onToggleSidebar();
        setTimeout(() => {
          isTransitioning.current = false;
        }, theme.transitions.duration.standard);
      }
    };

    if (sidebarOpen) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [sidebarOpen, onToggleSidebar, theme.transitions.duration.standard]);

  const getUniqueDates = () => {
    const dates = entries.map(entry => 
      new Date(entry.created_at).toLocaleDateString()
    );
    return Array.from(new Set(dates)).sort((a, b) => 
      new Date(b).getTime() - new Date(a).getTime()
    );
  };

  const hasEntriesForToday = () => {
    const today = new Date().toLocaleDateString();
    return entries.some(entry => 
      new Date(entry.created_at).toLocaleDateString() === today
    );
  };

  const handleDateClick = (date: string) => {
    if (selectedDate === date) {
      onDateSelect(null);
    } else {
      onDateSelect(date);
    }
  };

  const handleToggleClick = (e: React.MouseEvent) => {
    const now = Date.now();
    if (isTransitioning.current || now - lastClickTime.current < 300) return;
    
    e.preventDefault();
    e.stopPropagation();
    lastClickTime.current = now;
    isTransitioning.current = true;
    onToggleSidebar();
    setTimeout(() => {
      isTransitioning.current = false;
    }, theme.transitions.duration.standard);
  };

  return (
    <>
      <IconButton 
        ref={toggleRef}
        onClick={handleToggleClick}
        sx={{ 
          position: 'fixed',
          left: sidebarOpen ? SIDEBAR_WIDTH : 0,
          top: '80px',
          zIndex: 1201,
          bgcolor: theme.palette.background.default,
          color: theme.palette.text.primary,
          border: `1px solid ${theme.palette.divider}`,
          borderLeft: 'none',
          borderRadius: '0 4px 4px 0',
          width: '32px',
          height: '32px',
          transition: theme => theme.transitions.create(['left', 'transform'], {
            easing: theme.transitions.easing.easeInOut,
            duration: theme.transitions.duration.standard,
          }),
          transform: sidebarOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          '&:hover': {
            bgcolor: theme.palette.action.hover,
            transform: sidebarOpen ? 'rotate(180deg) scale(1.1)' : 'rotate(0deg) scale(1.1)',
          },
          '&:active': {
            transform: sidebarOpen ? 'rotate(180deg) scale(0.95)' : 'rotate(0deg) scale(0.95)',
          }
        }}
      >
        <MenuIcon sx={{ fontSize: '1.2rem' }} />
      </IconButton>

      <Drawer
        ref={sidebarRef}
        variant="temporary"
        open={sidebarOpen}
        onClose={onToggleSidebar}
        sx={{
          '& .MuiDrawer-paper': {
            width: SIDEBAR_WIDTH,
            boxSizing: 'border-box',
            bgcolor: theme.palette.background.default,
            borderRight: `1px solid ${theme.palette.divider}`,
            position: 'fixed',
            top: '64px',
            height: 'calc(100vh - 64px)',
            transition: theme => theme.transitions.create('transform', {
              easing: theme.transitions.easing.easeInOut,
              duration: theme.transitions.duration.standard,
            }),
          },
        }}
      >
        <List>
          {!hasEntriesForToday() && (
            <ListItemButton 
              onClick={() => onDateSelect(null)}
              selected={selectedDate === null}
              sx={{
                '&.Mui-selected': {
                  bgcolor: theme.palette.action.selected,
                  '&:hover': {
                    bgcolor: theme.palette.action.selected,
                  }
                }
              }}
            >
              <ListItemText primary="Today" />
            </ListItemButton>
          )}
          {getUniqueDates().map((date) => (
            <ListItemButton 
              key={date} 
              onClick={() => handleDateClick(date)}
              selected={selectedDate === date}
              sx={{
                '&.Mui-selected': {
                  bgcolor: theme.palette.action.selected,
                  '&:hover': {
                    bgcolor: theme.palette.action.selected,
                  }
                }
              }}
            >
              <ListItemText primary={date} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
    </>
  );
};

export default SharedSidebar; 