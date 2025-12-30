import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './BranchSelector.css';

const BranchSelector = () => {
  const { user, currentBranch, branches, fetchBranches, switchBranch, getBranchId } = useAuth();
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

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

  return (
    <div className="branch-selector">
      <button
        className="branch-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
      >
        <span className="branch-icon">🏢</span>
        <span className="branch-name">{currentBranchName}</span>
        <span className="branch-arrow">{isOpen ? '▲' : '▼'}</span>
      </button>
      
      {isOpen && (
        <>
          <div className="branch-overlay" onClick={() => setIsOpen(false)} />
          <div className="branch-dropdown">
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
                    <span className="branch-item-name">{branch.name}</span>
                    <span className="branch-item-city">{branch.city}</span>
                    {currentBranch && currentBranch.id === branch.id && (
                      <span className="branch-check">✓</span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default BranchSelector;

