import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/">Journal App</Link>
      </div>
      <div className="nav-links">
        {token ? (
          <>
            <Link to="/">Journal</Link>
            <Link to="/mood">Mood</Link>
            <Link to="/insights">Insights</Link>
            <button onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
      <ThemeToggle />
    </nav>
  );
};

export default Navbar; 