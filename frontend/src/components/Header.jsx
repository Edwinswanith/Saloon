import React from 'react';
import { FaBars } from 'react-icons/fa';
import './Header.css';

const Header = ({ title, onMenuClick }) => {
  return (
    <header className="app-header">
      <div className="header-left">
        {onMenuClick && (
          <button className="menu-icon" onClick={onMenuClick}>
            <FaBars />
          </button>
        )}
        <h1 className="header-title">{title}</h1>
      </div>
    </header>
  );
};

export default Header;

