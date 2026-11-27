import { apiGet, apiPost, apiPostForm } from './api';

export const CAMPAIGN_TEMPLATE_NAME = 'priyanka_promotional_offer';
export const CAMPAIGN_TEMPLATE_LANGUAGE = 'en_US';
export const MAX_CAMPAIGN_IMAGE_BYTES = 3 * 1024 * 1024;

export const normalizeCampaignPhone = (value) => {
  const raw = String(value || '').trim();
  if (!raw || !/^[+0-9 ().-]+$/.test(raw)) return '';

  let digits = raw.replace(/\D/g, '');
  if (digits.length === 11 && digits.startsWith('0')) digits = digits.slice(1);
  if (digits.length === 10 && /^[6-9]/.test(digits)) digits = `91${digits}`;
  return /^91[6-9][0-9]{9}$/.test(digits) ? digits : '';
};

export const analyzeCampaignSelection = (customers, selectedCustomers) => {
  const selected = customers.filter(customer => selectedCustomers.has(customer.id));
  let consented = 0;
  let eligible = 0;
  let excludedNoConsent = 0;
  let excludedInvalidPhone = 0;

  selected.forEach(customer => {
    if (customer.whatsapp_consent !== true) {
      excludedNoConsent += 1;
      return;
    }
    consented += 1;
    if (normalizeCampaignPhone(customer.mobile)) eligible += 1;
    else excludedInvalidPhone += 1;
  });

  return {
    selected: selected.length,
    consented,
    eligible,
    excludedNoConsent,
    excludedInvalidPhone,
    excluded: excludedNoConsent + excludedInvalidPhone,
  };
};

const readJson = async (response) => {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Campaign request failed.');
  return data;
};

export const uploadCampaignImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file, file.name);
  const response = await apiPostForm('/api/campaigns/media', formData);
  const data = await readJson(response);
  if (!data.media?.id) throw new Error('The uploaded image could not be identified.');
  return data.media.id;
};

export const createQueuedCampaign = async ({
  name,
  messageText,
  filterType,
  customerIds,
  campaignType,
  mediaAssetId,
}) => {
  if (!globalThis.crypto?.randomUUID) {
    throw new Error('This browser cannot create a secure campaign request ID.');
  }
  const requestId = globalThis.crypto.randomUUID();
  const response = await apiPost('/api/campaigns/send', {
    name,
    message_text: messageText,
    filter_type: filterType,
    customer_ids: customerIds,
    campaign_type: campaignType,
    delivery_method: 'api',
    request_id: requestId,
    template_name: CAMPAIGN_TEMPLATE_NAME,
    language: CAMPAIGN_TEMPLATE_LANGUAGE,
    media_asset_id: mediaAssetId,
  }, {
    headers: { 'Idempotency-Key': requestId },
  });
  const data = await readJson(response);
  if (response.status !== 202 && !data.duplicate) {
    throw new Error('The campaign was not accepted into the queue.');
  }
  return data;
};

export const getCampaignProgress = async (campaignId, options = {}) => {
  const response = await apiGet(`/api/campaigns/${campaignId}`, options);
  return readJson(response);
};

export const processQueuedCampaignBatch = async (campaignId, options = {}) => {
  const response = await apiPost('/api/campaigns/process-queue', {
    campaign_id: campaignId,
  }, options);
  return readJson(response);
};
