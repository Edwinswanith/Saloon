import React, { useState, useEffect } from 'react';
import Header from './Header';
import './DiscountApprovals.css';
import { useAuth } from '../contexts/AuthContext';
import { apiGet, apiPost } from '../utils/api';
import { showSuccess, showError, showWarning } from '../utils/toast.jsx';

const DiscountApprovals = () => {
  const { user, currentBranch } = useAuth()
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [approvalMethod, setApprovalMethod] = useState('in_app');
  const [approvalCode, setApprovalCode] = useState('');

  // All hooks must be called before any conditional return
  useEffect(() => {
    if (user && user.role === 'owner') {
      fetchApprovals();
    }
  }, [currentBranch]);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      const response = await apiGet('/api/discount-approvals?status=pending');
      if (!response.ok) throw new Error('Failed to fetch approvals');
      const data = await response.json();
      setApprovals(data.approvals || []);
    } catch (error) {
      console.error('Error fetching approvals:', error);
      showError('Failed to load discount approvals');
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
          showWarning('Please enter approval code');
          return;
        }
        response = await apiPost(`/api/discount-approvals/${selectedApproval.id}/approve-with-code`, {
          code: approvalCode
        });
      } else {
        response = await apiPost(`/api/discount-approvals/${selectedApproval.id}/approve`);
      }

      if (response.ok) {
        showSuccess('Discount approved successfully');
        setShowApproveModal(false);
        setSelectedApproval(null);
        setApprovalCode('');
        fetchApprovals();
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        showError(errorData.error || 'Failed to approve discount');
      }
    } catch (error) {
      console.error('Error approving discount:', error);
      showError('Error approving discount');
    }
  };

  const handleReject = async (approvalId) => {
    if (!window.confirm('Are you sure you want to reject this discount request?')) return;

    try {
      const response = await apiPost(`/api/discount-approvals/${approvalId}/reject`, { notes: '' });

      if (response.ok) {
        showSuccess('Discount request rejected');
        fetchApprovals();
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        showError(errorData.error || 'Failed to reject discount');
      }
    } catch (error) {
      console.error('Error rejecting discount:', error);
      showError('Error rejecting discount');
    }
  };

  // Restrict access to owners only — after all hooks
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
                    <td>{approval.requested_discount_amount?.toFixed(2)}</td>
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
                <p><strong>Discount:</strong> {selectedApproval.requested_discount_percent?.toFixed(2)}% ({selectedApproval.requested_discount_amount?.toFixed(2)})</p>
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
