import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('token');

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
          Journal App
        </Link>
      </div>
      <div className="nav-links">
        {token ? (
          <>
            <Link to="/mood" className={location.pathname === '/mood' ? 'active' : ''}>Mood</Link>
            <Link to="/insights" className={location.pathname === '/insights' ? 'active' : ''}>Insights</Link>
            <button onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className={location.pathname === '/login' ? 'active' : ''}>Login</Link>
            <Link to="/register" className={location.pathname === '/register' ? 'active' : ''}>Register</Link>
          </>
        )}
      </div>
      <ThemeToggle />
    </nav>
  );
};

export default Navbar; 