import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import Header from './Header';
import { FaExclamationTriangle } from 'react-icons/fa';
import './ApprovalCodes.css';

const ApprovalCodes = () => {
  const [codes, setCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generatedCode, setGeneratedCode] = useState(null);
  const [formData, setFormData] = useState({
    role: 'manager',
    max_uses: '',
    expires_in_days: ''
  });

  useEffect(() => {
    fetchCodes();
  }, []);

  const fetchCodes = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/discount-approvals/approval-codes`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      const data = await response.json();
      setCodes(data.codes || []);
    } catch (error) {
      console.error('Error fetching codes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/api/discount-approvals/approval-codes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          role: formData.role,
          max_uses: formData.max_uses ? parseInt(formData.max_uses) : null,
          expires_in_days: formData.expires_in_days ? parseInt(formData.expires_in_days) : null
        })
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedCode(data.code);
        setFormData({ role: 'manager', max_uses: '', expires_in_days: '' });
        fetchCodes();
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to generate code');
      }
    } catch (error) {
      console.error('Error generating code:', error);
      alert('Error generating approval code');
    }
  };

  const handleDeactivate = async (codeId) => {
    if (!confirm('Are you sure you want to deactivate this code?')) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/discount-approvals/approval-codes/${codeId}/deactivate`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        alert('Code deactivated');
        fetchCodes();
      }
    } catch (error) {
      console.error('Error deactivating code:', error);
    }
  };

  return (
    <div className="approval-codes-page">
      <Header title="Approval Codes" />
      <div className="page-content">
        <div className="page-header">
          <h2>Discount Approval Codes</h2>
          <button onClick={() => setShowGenerateModal(true)} className="btn-primary">
            Generate New Code
          </button>
        </div>

        {/* Generated Code Display */}
        {generatedCode && (
          <div className="generated-code-alert">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FaExclamationTriangle size={18} color="#f59e0b" /> IMPORTANT: Save this code securely!
            </h3>
            <p className="code-display">{generatedCode}</p>
            <p>This code will not be shown again. Copy it now!</p>
            <button onClick={() => {
              navigator.clipboard.writeText(generatedCode);
              alert('Code copied to clipboard!');
            }} className="btn-copy">
              Copy Code
            </button>
            <button onClick={() => setGeneratedCode(null)} className="btn-close">
              Close
            </button>
          </div>
        )}

        {/* Codes Table */}
        <div className="codes-table">
          <table>
            <thead>
              <tr>
                <th>Role</th>
                <th>Usage Count</th>
                <th>Max Uses</th>
                <th>Expires At</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7">Loading...</td></tr>
              ) : codes.length === 0 ? (
                <tr><td colSpan="7">No approval codes</td></tr>
              ) : (
                codes.map(code => (
                  <tr key={code.id}>
                    <td>{code.role}</td>
                    <td>{code.usage_count || 0}</td>
                    <td>{code.max_uses || 'Unlimited'}</td>
                    <td>{code.expires_at ? new Date(code.expires_at).toLocaleDateString() : 'Never'}</td>
                    <td>
                      <span className={`status-badge ${code.is_active && !code.is_expired && code.can_use ? 'active' : 'inactive'}`}>
                        {code.is_active && !code.is_expired && code.can_use ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>{new Date(code.created_at).toLocaleDateString()}</td>
                    <td>
                      {code.is_active && (
                        <button
                          onClick={() => handleDeactivate(code.id)}
                          className="btn-deactivate"
                        >
                          Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Generate Modal */}
        {showGenerateModal && (
          <div className="modal-overlay" onClick={() => { setShowGenerateModal(false); setFormData({ role: 'manager', max_uses: '', expires_in_days: '' }); }}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Generate Approval Code</h2>
              <form onSubmit={handleGenerate}>
                <div className="form-group">
                  <label>Role *</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    required
                  >
                    <option value="manager">Manager</option>
                    <option value="owner">Owner</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Max Uses (Optional)</label>
                  <input
                    type="number"
                    value={formData.max_uses}
                    onChange={(e) => setFormData({...formData, max_uses: e.target.value})}
                    placeholder="Leave empty for unlimited"
                    min="1"
                  />
                </div>
                <div className="form-group">
                  <label>Expires In Days (Optional)</label>
                  <input
                    type="number"
                    value={formData.expires_in_days}
                    onChange={(e) => setFormData({...formData, expires_in_days: e.target.value})}
                    placeholder="Leave empty for no expiration"
                    min="1"
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" onClick={() => { setShowGenerateModal(false); setFormData({ role: 'manager', max_uses: '', expires_in_days: '' }); }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">Generate Code</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApprovalCodes;

