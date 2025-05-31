import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import './styles/theme.css';
import './App.css';

// Import your pages here
import Login from './pages/Login';
import Register from './pages/Register';
import Journal from './pages/Journal';
import Insights from './pages/Insights';
import Mood from './pages/Mood';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="App">
          <Navbar />
          <main className="main-content">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/" element={<Journal />} />
              <Route path="/insights" element={<Insights />} />
              <Route path="/mood" element={<Mood />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
