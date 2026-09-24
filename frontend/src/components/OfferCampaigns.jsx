import React, { useState, useEffect } from 'react';
import Header from './Header';
import GeneralCampaign from './GeneralCampaign';
import BirthdayCampaign from './BirthdayCampaign';
import './OfferCampaigns.css';
import { apiGet } from '../utils/api';
import { showError } from '../utils/toast.jsx';
import { useAuth } from '../contexts/AuthContext';
import CompactSelect from './shared/CompactSelect';

const CAMPAIGN_TYPE_FILTER_OPTIONS = [
  { value: 'all', label: 'All Campaigns' },
  { value: 'general', label: 'General Only' },
  { value: 'birthday', label: 'Birthday Only' },
];

const OfferCampaigns = () => {
  const { currentBranch } = useAuth();
  const [activeTab, setActiveTab] = useState('general'); // 'general' or 'birthday'
  const [campaigns, setCampaigns] = useState([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [campaignTypeFilter, setCampaignTypeFilter] = useState('all'); // 'all', 'general', 'birthday'

  useEffect(() => {
    fetchCampaigns();
  }, [campaignTypeFilter, currentBranch]);

  const fetchCampaigns = async () => {
    try {
      setLoadingCampaigns(true);
      const url = campaignTypeFilter === 'all'
        ? '/api/campaigns'
        : `/api/campaigns?type=${campaignTypeFilter}`;
      const response = await apiGet(url);
      if (!response.ok) throw new Error('Failed to fetch campaigns');
      const data = await response.json();
      setCampaigns(data.campaigns || []);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      showError('Failed to load campaign history');
    } finally {
      setLoadingCampaigns(false);
    }
  };

  const handleCampaignSent = () => {
    fetchCampaigns();
  };

  return (
    <div className="offer-campaigns-page">
      <Header title="Offer Campaigns" />
      <div className="page-content">
        {/* Tab Navigation */}
        <div className="campaign-tabs">
          <button
            className={`tab-button ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            General Offer Campaigns
          </button>
          <button
            className={`tab-button ${activeTab === 'birthday' ? 'active' : ''}`}
            onClick={() => setActiveTab('birthday')}
          >
            Birthday Offer Campaigns
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'general' && (
          <GeneralCampaign onCampaignSent={handleCampaignSent} />
        )}
        {activeTab === 'birthday' && (
          <BirthdayCampaign onCampaignSent={handleCampaignSent} />
        )}

        {/* Campaign History */}
        <div className="campaign-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2>Campaign History</h2>
            <div style={{ maxWidth: '200px', width: '100%' }}>
              <CompactSelect
                value={campaignTypeFilter}
                onChange={(v) => setCampaignTypeFilter(v)}
                className="filter-select"
                options={CAMPAIGN_TYPE_FILTER_OPTIONS}
                placeholder="All Campaigns"
              />
            </div>
          </div>
          {loadingCampaigns ? (
            <div className="loading-state">Loading campaigns...</div>
          ) : campaigns.length === 0 ? (
            <div className="empty-state">No campaigns sent yet</div>
          ) : (
            <div className="campaigns-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Filter</th>
                    <th>Sent</th>
                    <th>Failed</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map(campaign => (
                    <tr key={campaign.id}>
                      <td>{campaign.name}</td>
                      <td>
                        <span className={`type-badge ${campaign.campaign_type || 'general'}`}>
                          {campaign.campaign_type === 'birthday' ? 'Birthday' : 'General'}
                        </span>
                      </td>
                      <td>{campaign.filter_type}</td>
                      <td>{campaign.sent_count}</td>
                      <td>{campaign.failed_count}</td>
                      <td>
                        <span className={`status-badge ${campaign.status}`}>
                          {campaign.status}
                        </span>
                      </td>
                      <td>{new Date(campaign.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OfferCampaigns;
