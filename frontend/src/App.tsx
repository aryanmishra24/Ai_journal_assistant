import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Layout from './components/Layout';
import './styles/theme.css';
import './App.css';

// Import your pages here
import Login from './pages/Login';
import Register from './pages/Register';
import Journal from './pages/Journal';
import Insights from './pages/Insights';
import Mood from './pages/Mood';
import { JournalEntry, Mood as MoodType } from './services/api';

// Create a wrapper component to access location
const AppContent: React.FC = () => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>([]);
  const [moodEntries, setMoodEntries] = useState<MoodType[]>([]);

  // Determine the current page type
  const getPageType = () => {
    if (location.pathname === '/mood') return 'mood';
    if (location.pathname === '/') return 'journal';
    return 'journal'; // default
  };

  const handleToggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  // Get the appropriate entries based on the current page type
  const getEntries = () => {
    const type = getPageType();
    return type === 'mood' ? moodEntries : journalEntries;
  };

  return (
    <div className="App">
      <Navbar />
      <Layout
        type={getPageType()}
        entries={getEntries()}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={handleToggleSidebar}
        selectedDate={selectedDate}
        onDateSelect={setSelectedDate}
      >
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route 
            path="/" 
            element={
              <Journal 
                selectedDate={selectedDate} 
                onDateSelect={setSelectedDate}
                sidebarOpen={sidebarOpen}
                onToggleSidebar={handleToggleSidebar}
                entries={journalEntries}
                setEntries={setJournalEntries}
              />
            } 
          />
          <Route path="/insights" element={<Insights />} />
          <Route 
            path="/mood" 
            element={
              <Mood 
                selectedDate={selectedDate} 
                onDateSelect={setSelectedDate}
                sidebarOpen={sidebarOpen}
                onToggleSidebar={handleToggleSidebar}
                entries={moodEntries}
                setEntries={setMoodEntries}
              />
            } 
          />
        </Routes>
      </Layout>
    </div>
  );
};

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
}

export default App;
