import React, { useState, useEffect } from 'react';
import { apiGet, apiPut } from '../utils/api';
import Header from './Header';
import './ServiceRecovery.css';
import { useAuth } from '../contexts/AuthContext';

const ServiceRecovery = () => {
  const { currentBranch } = useAuth()
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, open: 0, in_progress: 0, resolved: 0, closed: 0, resolution_rate: 0 });
  const [filters, setFilters] = useState({ status: '', issue_type: '', assigned_manager_id: '' });
  const [managers, setManagers] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveNotes, setResolveNotes] = useState('');

  useEffect(() => {
    fetchCases();
    fetchStats();
    fetchManagers();
  }, [filters, currentBranch]);

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[ServiceRecovery] Branch changed, refreshing data...')
      fetchCases()
      fetchStats()
      fetchManagers()
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  const fetchCases = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.issue_type) params.append('issue_type', filters.issue_type);
      if (filters.assigned_manager_id) params.append('assigned_manager_id', filters.assigned_manager_id);

      const endpoint = `/api/service-recovery${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await apiGet(endpoint);
      const data = await response.json();
      setCases(data.cases || []);
    } catch (error) {
      console.error('Error fetching cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await apiGet('/api/service-recovery/stats');
      const data = await response.json();
      setStats(data.stats || stats);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchManagers = async () => {
    try {
      const response = await apiGet('/api/managers?role=manager');
      const data = await response.json();
      setManagers(Array.isArray(data) ? data : (data.managers || []));
    } catch (error) {
      console.error('Error fetching managers:', error);
    }
  };

  const handleAssign = async (caseId, managerId) => {
    try {
      const response = await apiPut(`/api/service-recovery/${caseId}/assign`, { manager_id: managerId });

      if (response.ok) {
        fetchCases();
        fetchStats();
      }
    } catch (error) {
      console.error('Error assigning manager:', error);
    }
  };

  const handleResolve = async () => {
    if (!selectedCase) return;

    try {
      const response = await apiPut(`/api/service-recovery/${selectedCase.id}/resolve`, { resolution_notes: resolveNotes });

      if (response.ok) {
        setShowResolveModal(false);
        setSelectedCase(null);
        setResolveNotes('');
        fetchCases();
        fetchStats();
      }
    } catch (error) {
      console.error('Error resolving case:', error);
    }
  };

  return (
    <div className="service-recovery-page">
      <Header title="Service Recovery Cases" />
      <div className="page-content">
        {/* Statistics */}
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Cases</h3>
            <p className="stat-value">{stats.total}</p>
          </div>
          <div className="stat-card">
            <h3>Open</h3>
            <p className="stat-value">{stats.open}</p>
          </div>
          <div className="stat-card">
            <h3>In Progress</h3>
            <p className="stat-value">{stats.in_progress}</p>
          </div>
          <div className="stat-card">
            <h3>Resolved</h3>
            <p className="stat-value">{stats.resolved}</p>
          </div>
          <div className="stat-card">
            <h3>Resolution Rate</h3>
            <p className="stat-value">{stats.resolution_rate}%</p>
          </div>
        </div>

        {/* Filters */}
        <div className="filters-section">
          <select value={filters.status} onChange={(e) => setFilters({...filters, status: e.target.value})}>
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <select value={filters.issue_type} onChange={(e) => setFilters({...filters, issue_type: e.target.value})}>
            <option value="">All Issue Types</option>
            <option value="service_quality">Service Quality</option>
            <option value="staff_behavior">Staff Behavior</option>
            <option value="pricing">Pricing</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Cases Table */}
        <div className="cases-table">
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Issue Type</th>
                <th>Description</th>
                <th>Assigned Manager</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7">Loading...</td></tr>
              ) : cases.length === 0 ? (
                <tr><td colSpan="7">No cases found</td></tr>
              ) : (
                cases.map(caseItem => (
                  <tr key={caseItem.id}>
                    <td>{caseItem.customer_name || '-'}</td>
                    <td>{caseItem.issue_type}</td>
                    <td>{caseItem.description?.substring(0, 50)}...</td>
                    <td>
                      {caseItem.assigned_manager_name ? (
                        caseItem.assigned_manager_name
                      ) : (
                        <select
                          value=""
                          onChange={(e) => handleAssign(caseItem.id, e.target.value)}
                        >
                          <option value="">Assign Manager</option>
                          {managers.map(manager => (
                            <option key={manager.id} value={manager.id}>
                              {manager.firstName} {manager.lastName}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge status-${caseItem.status}`}>
                        {caseItem.status}
                      </span>
                    </td>
                    <td>{new Date(caseItem.created_at).toLocaleDateString()}</td>
                    <td>
                      {caseItem.status !== 'resolved' && caseItem.status !== 'closed' && (
                        <button
                          onClick={() => {
                            setSelectedCase(caseItem);
                            setShowResolveModal(true);
                          }}
                          className="btn-resolve"
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Resolve Modal */}
        {showResolveModal && selectedCase && (
          <div className="modal-overlay" onClick={() => { setShowResolveModal(false); setSelectedCase(null); setResolveNotes(''); }}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>Resolve Service Recovery Case</h2>
              <div className="case-details">
                <p><strong>Customer:</strong> {selectedCase.customer_name}</p>
                <p><strong>Issue Type:</strong> {selectedCase.issue_type}</p>
                <p><strong>Description:</strong> {selectedCase.description}</p>
              </div>
              <div className="form-group">
                <label>Resolution Notes *</label>
                <textarea
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  rows="5"
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => { setShowResolveModal(false); setSelectedCase(null); setResolveNotes(''); }}>
                  Cancel
                </button>
                <button onClick={handleResolve} className="btn-primary">Resolve Case</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ServiceRecovery;

