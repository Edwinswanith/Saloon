import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../contexts/AuthContext';
import './BranchSelector.css';

const BranchSelector = () => {
  const { user, currentBranch, branches, fetchBranches, switchBranch, getBranchId } = useAuth();
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, right: 0 });
  const buttonRef = useRef(null);

  useEffect(() => {
    // Fetch branches on mount if user is Owner
    if (user && user.role === 'owner' && branches.length === 0) {
      fetchBranches();
    }
  }, [user, branches.length, fetchBranches]);

  // Only show for Owner
  if (!user || user.role !== 'owner') {
    return null;
  }

  const handleBranchChange = async (branchId) => {
    setLoading(true);
    try {
      const result = await switchBranch(branchId);
      if (result.success) {
        setIsOpen(false);
        // Dispatch custom event to notify all components about branch change
        window.dispatchEvent(new CustomEvent('branchChanged', { 
          detail: { branchId, branch: result.branch } 
        }));
      } else {
        alert(result.error || 'Failed to switch branch');
      }
    } catch (error) {
      console.error('Branch switch error:', error);
      alert('Failed to switch branch');
    } finally {
      setLoading(false);
    }
  };

  const currentBranchName = currentBranch ? currentBranch.name : 'Select Branch';

  const handleToggle = () => {
    if (!isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const vw = window.innerWidth;
      const margin = 8;
      const dropdownWidth = Math.min(400, vw - margin * 2);
      // Anchor right edge to button, but clamp so it never overflows viewport
      let right = vw - rect.right;
      const left = vw - right - dropdownWidth;
      if (left < margin) {
        right = vw - dropdownWidth - margin;
      }
      setDropdownPosition({
        top: rect.bottom + 8,
        right: Math.max(margin, right),
        width: dropdownWidth
      });
    }
    setIsOpen(!isOpen);
  };

  return (
    <div className="branch-selector">
      <button
        ref={buttonRef}
        className="branch-selector-button"
        onClick={handleToggle}
        disabled={loading}
      >
        <span className="branch-name">{currentBranchName}</span>
        <span className="branch-arrow">{isOpen ? '▲' : '▼'}</span>
      </button>
      
      {isOpen && typeof document !== 'undefined' && createPortal(
        <>
          <div className="branch-overlay" onClick={() => setIsOpen(false)} />
          <div 
            className="branch-dropdown"
            style={{
              top: `${dropdownPosition.top}px`,
              right: `${dropdownPosition.right}px`,
              width: `${dropdownPosition.width}px`
            }}
          >
            <div className="branch-dropdown-header">
              <span>Select Branch</span>
              <button className="branch-close" onClick={() => setIsOpen(false)}>×</button>
            </div>
            <div className="branch-list">
              {branches.length === 0 ? (
                <div className="branch-loading">Loading branches...</div>
              ) : (
                branches.map((branch) => (
                  <button
                    key={branch.id}
                    className={`branch-item ${currentBranch && currentBranch.id === branch.id ? 'active' : ''}`}
                    onClick={() => handleBranchChange(branch.id)}
                    disabled={loading || (currentBranch && currentBranch.id === branch.id)}
                  >
                    <div className="branch-item-content">
                      <span className="branch-item-name">{branch.name}</span>
                      <span className="branch-item-city">{branch.city}</span>
                    </div>
                    {currentBranch && currentBranch.id === branch.id && (
                      <span className="branch-check">✓</span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
};

export default BranchSelector;

