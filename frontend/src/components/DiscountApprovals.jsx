import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import Header from './Header';
import './DiscountApprovals.css';
import { useAuth } from '../contexts/AuthContext';

const DiscountApprovals = () => {
  const { user, currentBranch } = useAuth()
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [approvalMethod, setApprovalMethod] = useState('in_app'); // 'in_app' or 'code'
  const [approvalCode, setApprovalCode] = useState('');
  
  // Restrict access to owners only
  if (!user || user.role !== 'owner') {
    return (
      <div style={{ 
        padding: '40px', 
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px'
      }}>
        <h2 style={{ color: '#dc2626', marginBottom: '16px' }}>Access Denied</h2>
        <p style={{ color: '#6b7280', fontSize: '16px' }}>
          Only owners can access discount approvals.
        </p>
      </div>
    );
  }

  useEffect(() => {
    fetchApprovals();
  }, [currentBranch]);

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[DiscountApprovals] Branch changed, refreshing approvals...')
      fetchApprovals()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/discount-approvals?status=pending`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      const data = await response.json();
      setApprovals(data.approvals || []);
    } catch (error) {
      console.error('Error fetching approvals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedApproval) return;

    try {
      let response;
      if (approvalMethod === 'code') {
        if (!approvalCode) {
          alert('Please enter approval code');
          return;
        }
        response = await fetch(`${API_BASE_URL}/api/discount-approvals/${selectedApproval.id}/approve-with-code`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          },
          body: JSON.stringify({ code: approvalCode })
        });
      } else {
        response = await fetch(`${API_BASE_URL}/api/discount-approvals/${selectedApproval.id}/approve`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          }
        });
      }

      if (response.ok) {
        alert('Discount approved successfully');
        setShowApproveModal(false);
        setSelectedApproval(null);
        setApprovalCode('');
        fetchApprovals();
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to approve discount');
      }
    } catch (error) {
      console.error('Error approving discount:', error);
      alert('Error approving discount');
    }
  };

  const handleReject = async (approvalId, notes = '') => {
    if (!confirm('Are you sure you want to reject this discount request?')) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/discount-approvals/${approvalId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ notes })
      });

      if (response.ok) {
        alert('Discount request rejected');
        fetchApprovals();
      }
    } catch (error) {
      console.error('Error rejecting discount:', error);
    }
  };

  return (
    <div className="discount-approvals-page">
      <Header title="Discount Approvals" />
      <div className="page-content">
        <div className="approvals-table">
          <table>
            <thead>
              <tr>
                <th>Bill Number</th>
                <th>Requested By</th>
                <th>Discount %</th>
                <th>Discount Amount</th>
                <th>Reason</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7">Loading...</td></tr>
              ) : approvals.length === 0 ? (
                <tr><td colSpan="7">No pending approvals</td></tr>
              ) : (
                approvals.map(approval => (
                  <tr key={approval.id}>
                    <td>{approval.bill_number || '-'}</td>
                    <td>{approval.requested_by_name || '-'}</td>
                    <td>{approval.requested_discount_percent?.toFixed(2)}%</td>
                    <td>₹{approval.requested_discount_amount?.toFixed(2)}</td>
                    <td>{approval.reason || '-'}</td>
                    <td>{new Date(approval.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        onClick={() => {
                          setSelectedApproval(approval);
                          setShowApproveModal(true);
                        }}
                        className="btn-approve"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(approval.id)}
                        className="btn-reject"
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Approve Modal */}
        {showApproveModal && selectedApproval && (
          <div className="modal-overlay" onClick={() => { setShowApproveModal(false); setSelectedApproval(null); setApprovalCode(''); }}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Approve Discount</h2>
              <div className="approval-details">
                <p><strong>Bill Number:</strong> {selectedApproval.bill_number}</p>
                <p><strong>Requested By:</strong> {selectedApproval.requested_by_name}</p>
                <p><strong>Discount:</strong> {selectedApproval.requested_discount_percent?.toFixed(2)}% (₹{selectedApproval.requested_discount_amount?.toFixed(2)})</p>
                <p><strong>Reason:</strong> {selectedApproval.reason}</p>
              </div>
              <div className="form-group">
                <label>Approval Method</label>
                <select value={approvalMethod} onChange={(e) => setApprovalMethod(e.target.value)}>
                  <option value="in_app">In-App Approval</option>
                  <option value="code">Approval Code</option>
                </select>
              </div>
              {approvalMethod === 'code' && (
                <div className="form-group">
                  <label>Approval Code *</label>
                  <input
                    type="text"
                    value={approvalCode}
                    onChange={(e) => setApprovalCode(e.target.value)}
                    placeholder="Enter approval code"
                    required
                  />
                </div>
              )}
              <div className="modal-actions">
                <button type="button" onClick={() => { setShowApproveModal(false); setSelectedApproval(null); setApprovalCode(''); }}>
                  Cancel
                </button>
                <button onClick={handleApprove} className="btn-primary">Approve</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DiscountApprovals;

