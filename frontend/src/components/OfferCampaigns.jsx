import React, { useCallback, useEffect, useState } from 'react';
import Header from './Header';
import GeneralCampaign from './GeneralCampaign';
import BirthdayCampaign from './BirthdayCampaign';
import './OfferCampaigns.css';
import { apiGet, apiPost } from '../utils/api';
import {
  getCampaignProgress,
  processQueuedCampaignBatch,
} from '../utils/campaignQueue';
import { showError, showSuccess } from '../utils/toast.jsx';
import { useAuth } from '../contexts/AuthContext';
import CompactSelect from './shared/CompactSelect';

const CAMPAIGN_TYPE_FILTER_OPTIONS = [
  { value: 'all', label: 'All Campaigns' },
  { value: 'general', label: 'General Only' },
  { value: 'birthday', label: 'Birthday Only' },
];

const ACTIVE_CAMPAIGN_STATUSES = ['queued', 'processing', 'in_progress'];
const STOP_CAMPAIGN_STATUSES = ['paused', 'completed', 'failed', 'attention_required', 'delivered', 'read'];

const waitFor = (milliseconds, signal) => new Promise(resolve => {
  if (signal.aborted) {
    resolve();
    return;
  }
  const timer = window.setTimeout(resolve, milliseconds);
  signal.addEventListener('abort', () => {
    window.clearTimeout(timer);
    resolve();
  }, { once: true });
});

const PROGRESS_FIELDS = [
  ['queued_count', 'Queued'],
  ['processing_count', 'Processing'],
  ['accepted_count', 'Accepted'],
  ['sent_count', 'Sent'],
  ['delivered_count', 'Delivered'],
  ['read_count', 'Read'],
  ['failed_count', 'Failed'],
  ['unknown_count', 'Unknown'],
  ['excluded_count', 'Excluded'],
];

const OfferCampaigns = () => {
  const { currentBranch } = useAuth();
  const [activeTab, setActiveTab] = useState('general'); // 'general' or 'birthday'
  const [campaigns, setCampaigns] = useState([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [campaignTypeFilter, setCampaignTypeFilter] = useState('all'); // 'all', 'general', 'birthday'
  const [activeCampaign, setActiveCampaign] = useState(null);
  const [processingRun, setProcessingRun] = useState(0);

  const fetchCampaigns = useCallback(async () => {
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
  }, [campaignTypeFilter]);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns, currentBranch]);

  useEffect(() => {
    if (!activeCampaign?.campaign_id) return undefined;
    const campaignId = activeCampaign.campaign_id;
    const controller = new AbortController();

    const continueCampaign = async () => {
      try {
        let progress = await getCampaignProgress(campaignId, {
          signal: controller.signal,
        });

        while (!controller.signal.aborted) {
          setActiveCampaign(progress);
          const status = progress.status;
          const queued = Number(progress.queued_count || 0);

          if (STOP_CAMPAIGN_STATUSES.includes(status)) {
            fetchCampaigns();
            return;
          }
          if (queued > 0) {
            if (!ACTIVE_CAMPAIGN_STATUSES.includes(status)) {
              fetchCampaigns();
              return;
            }
            const batch = await processQueuedCampaignBatch(campaignId, {
              signal: controller.signal,
            });
            progress = batch.campaign || await getCampaignProgress(campaignId, {
              signal: controller.signal,
            });
            setActiveCampaign(progress);
            if (batch.paused || STOP_CAMPAIGN_STATUSES.includes(progress.status)) {
              fetchCampaigns();
              return;
            }
            await waitFor(batch.deferred ? 60000 : 500, controller.signal);
            progress = await getCampaignProgress(campaignId, {
              signal: controller.signal,
            });
            continue;
          }

          if (!ACTIVE_CAMPAIGN_STATUSES.includes(status) || !progress.eligible_count) {
            fetchCampaigns();
            return;
          }
          await waitFor(5000, controller.signal);
          progress = await getCampaignProgress(campaignId, {
            signal: controller.signal,
          });
        }
      } catch (error) {
        if (!controller.signal.aborted && error.name !== 'AbortError') {
          showError(error.message || 'Campaign processing stopped unexpectedly.');
        }
      }
    };

    continueCampaign();
    return () => controller.abort();
  }, [activeCampaign?.campaign_id, fetchCampaigns, processingRun]);

  const handleCampaignSent = (campaign) => {
    if (campaign?.campaign_id) {
      setActiveCampaign(campaign);
      setProcessingRun(value => value + 1);
    }
    fetchCampaigns();
  };

  const resumeActiveCampaign = async () => {
    if (!activeCampaign?.campaign_id) return;
    try {
      const response = await apiPost(`/api/campaigns/${activeCampaign.campaign_id}/resume`, {});
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || 'Campaign could not be resumed.');
      setActiveCampaign(data);
      setProcessingRun(value => value + 1);
      showSuccess('Campaign resumed and returned to the queue.');
    } catch (error) {
      showError(error.message || 'Campaign could not be resumed.');
    }
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

        {activeCampaign && (
          <section className="campaign-section campaign-progress-panel" aria-live="polite">
            <div className="campaign-progress-header">
              <div>
                <h2>{activeCampaign.name || 'Campaign Progress'}</h2>
                <p>
                  Campaign started. This page continues secure server batches and updates the counts live.
                </p>
              </div>
              <div className="campaign-progress-status">
                <span className={`status-badge ${activeCampaign.status}`}>{activeCampaign.status}</span>
                {activeCampaign.status === 'paused' && (
                  <button type="button" className="btn-primary" onClick={resumeActiveCampaign}>Resume</button>
                )}
              </div>
            </div>
            <div className="campaign-progress-grid">
              {PROGRESS_FIELDS.map(([field, label]) => (
                <div className="campaign-progress-metric" key={field}>
                  <span>{label}</span>
                  <strong>{activeCampaign[field] || 0}</strong>
                </div>
              ))}
            </div>
            {activeCampaign.pause_reason && (
              <div className="campaign-pause-reason">Paused: {activeCampaign.pause_reason}</div>
            )}
          </section>
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
                    <th>Requested</th>
                    <th>Eligible</th>
                    <th>No Consent</th>
                    <th>Invalid Phone</th>
                    <th>Queued</th>
                    <th>Processing</th>
                    <th>Accepted</th>
                    <th>Sent</th>
                    <th>Delivered</th>
                    <th>Read</th>
                    <th>Failed</th>
                    <th>Unknown</th>
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
                      <td>{campaign.requested_count || 0}</td>
                      <td>{campaign.eligible_count || 0}</td>
                      <td>{campaign.excluded_no_consent || 0}</td>
                      <td>{campaign.excluded_invalid_phone || 0}</td>
                      <td>{campaign.queued_count || 0}</td>
                      <td>{campaign.processing_count || 0}</td>
                      <td>{campaign.accepted_count || 0}</td>
                      <td>{campaign.sent_count}</td>
                      <td>{campaign.delivered_count || 0}</td>
                      <td>{campaign.read_count || 0}</td>
                      <td>{campaign.failed_count}</td>
                      <td>{campaign.unknown_count || 0}</td>
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
