/**
 * Single API boundary. Pages never call fetch directly.
 * Session cookies are HttpOnly; mutations echo the per-session CSRF token.
 */

export const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

let csrfToken = null;
let unauthorizedHandler = null;

export class ApiError extends Error {
  constructor(message, { status = 0, code = '', details = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

export function setCsrfToken(token) {
  csrfToken = token;
}

export async function refreshCsrf() {
  try {
    const res = await fetch(`${API_BASE}/auth/csrf`, { credentials: 'include' });
    if (!res.ok) {
      csrfToken = null;
      return null;
    }
    const body = await res.json();
    csrfToken = body?.csrfToken || null;
    return csrfToken;
  } catch {
    csrfToken = null;
    return null;
  }
}

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value);
  });
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

export async function api(path, { method = 'GET', body, form, retry = true } = {}) {
  const headers = {};
  const init = { method, credentials: 'include', headers };

  if (form) {
    init.body = form;
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }

  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  const res = await fetch(`${API_BASE}${path}`, init);
  const text = await res.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!res.ok) {
    const error = payload?.error;
    if (res.status === 403 && error?.code === 'CSRF_INVALID' && retry) {
      await refreshCsrf();
      return api(path, { method, body, form, retry: false });
    }
    if (res.status === 401) unauthorizedHandler?.();
    throw new ApiError(error?.message || `Request failed (${res.status})`, {
      status: res.status,
      code: error?.code || '',
      details: error?.details ?? null,
    });
  }

  return payload;
}

export const publicApi = {
  config: () => api('/public/config'),
  edition: () => api('/public/editions/current'),
  editionBySlug: (slug) => api(`/public/editions/${encodeURIComponent(slug)}`),
  categories: (slug) => api(`/public/editions/${encodeURIComponent(slug)}/categories`),
  events: (slug, params = {}) =>
    api(`/public/editions/${encodeURIComponent(slug)}/events${query(params)}`),
  event: (slug, eventSlug) =>
    api(`/public/editions/${encodeURIComponent(slug)}/events/${encodeURIComponent(eventSlug)}`),
  schedule: (slug) => api(`/public/editions/${encodeURIComponent(slug)}/schedule`),
  announcements: (slug, params = {}) =>
    api(`/public/editions/${encodeURIComponent(slug)}/announcements${query(params)}`),
  policy: (slug) => api(`/public/editions/${encodeURIComponent(slug)}/policy`),
  iconUrl: (iconId) => `${API_BASE}/public/icons/${iconId}`,
  documentUrl: (relative) => (relative?.startsWith('http') ? relative : relative),
};

export const authApi = {
  login: (payload) => api('/auth/login', { method: 'POST', body: payload }),
  logout: () => api('/auth/logout', { method: 'POST' }),
  me: () => api('/me'),
  sessions: () => api('/me/sessions'),
  profile: () => api('/me/profile'),
  updateProfile: (payload) => api('/me/profile', { method: 'PATCH', body: payload }),
  googleLoginHref: (next = '/portal') =>
    `${API_BASE}/auth/google/login?next=${encodeURIComponent(next)}`,
};

export const portalApi = {
  pass: (editionId) => api(`/editions/${editionId}/pass`),
  createPassOrder: (editionId) => api(`/editions/${editionId}/pass/order`, { method: 'POST' }),
  saveSelections: (editionId, eventIds) =>
    api(`/editions/${editionId}/pass/selections`, { method: 'PUT', body: { eventIds } }),
  registrations: (editionId) => api(`/editions/${editionId}/registrations`),
  registerAddons: (editionId, eventIds) =>
    api(`/editions/${editionId}/registrations`, { method: 'POST', body: { eventIds } }),
  cancelRegistration: (editionId, registrationId) =>
    api(`/editions/${editionId}/registrations/${registrationId}`, { method: 'DELETE' }),
  teams: (editionId) => api(`/editions/${editionId}/teams`),
  createTeam: (editionId, payload) =>
    api(`/editions/${editionId}/teams`, { method: 'POST', body: payload }),
  joinTeam: (editionId, inviteCode) =>
    api(`/editions/${editionId}/teams/join`, { method: 'POST', body: { inviteCode } }),
  leaveTeam: (editionId, teamId) =>
    api(`/editions/${editionId}/teams/${teamId}`, { method: 'DELETE' }),
  rotateInvite: (editionId, teamId) =>
    api(`/editions/${editionId}/teams/${teamId}/rotate-invite`, { method: 'POST' }),
  verification: (editionId) => api(`/editions/${editionId}/verification`),
  submitVerification: (editionId, form) =>
    api(`/editions/${editionId}/verification`, { method: 'POST', form }),
  confirmVerification: (editionId, code) =>
    api(`/editions/${editionId}/verification/confirm`, { method: 'POST', body: { code } }),
  tickets: (editionId) => api(`/editions/${editionId}/tickets`),
  ticketQrUrl: (editionId, ticketId, accent = '') =>
    `${API_BASE}/editions/${editionId}/tickets/${ticketId}/qr${accent ? `?accent=${encodeURIComponent(accent)}` : ''}`,
  payment: (editionId, orderId) => api(`/editions/${editionId}/payments/${orderId}`),
  mockPay: (editionId, orderId) =>
    api(`/editions/${editionId}/payments/${orderId}/mock`, { method: 'POST' }),
};

const adminBase = (editionId) => `/editions/${editionId}/admin`;

export const adminApi = {
  overview: (editionId) => api(`${adminBase(editionId)}/overview`),
  permissions: (editionId) => api(`${adminBase(editionId)}/my-permissions`),
  settings: (editionId) => api(`${adminBase(editionId)}/settings`),
  updateSettings: (editionId, payload) =>
    api(`${adminBase(editionId)}/settings`, { method: 'PATCH', body: payload }),
  policies: (editionId) => api(`${adminBase(editionId)}/policies`),
  checkPolicy: (editionId, payload) =>
    api(`${adminBase(editionId)}/policies/check`, { method: 'POST', body: payload }),
  createPolicy: (editionId, payload) =>
    api(`${adminBase(editionId)}/policies`, { method: 'POST', body: payload }),
  categories: (editionId) => api(`${adminBase(editionId)}/categories`),
  createCategory: (editionId, payload) =>
    api(`${adminBase(editionId)}/categories`, { method: 'POST', body: payload }),
  updateCategory: (editionId, categoryId, payload) =>
    api(`${adminBase(editionId)}/categories/${categoryId}`, { method: 'PATCH', body: payload }),
  events: (editionId, params = {}) => api(`${adminBase(editionId)}/events${query(params)}`),
  event: (editionId, eventId) => api(`${adminBase(editionId)}/events/${eventId}`),
  createEvent: (editionId, payload) =>
    api(`${adminBase(editionId)}/events`, { method: 'POST', body: payload }),
  updateEvent: (editionId, eventId, payload) =>
    api(`${adminBase(editionId)}/events/${eventId}`, { method: 'PATCH', body: payload }),
  icons: (editionId) => api(`${adminBase(editionId)}/icons`),
  uploadIcon: (editionId, form) =>
    api(`${adminBase(editionId)}/icons`, { method: 'POST', form }),
  archiveIcon: (editionId, iconId) =>
    api(`${adminBase(editionId)}/icons/${iconId}`, { method: 'DELETE' }),
  users: (editionId, params = {}) => api(`${adminBase(editionId)}/users${query(params)}`),
  setUserStatus: (editionId, userId, payload) =>
    api(`${adminBase(editionId)}/users/${userId}/status`, { method: 'PATCH', body: payload }),
  memberships: (editionId) => api(`${adminBase(editionId)}/memberships`),
  grantMembership: (editionId, payload) =>
    api(`${adminBase(editionId)}/memberships`, { method: 'POST', body: payload }),
  inviteStaff: (editionId, payload) =>
    api(`${adminBase(editionId)}/staff-invites`, { method: 'POST', body: payload }),
  payments: (editionId, params = {}) => api(`${adminBase(editionId)}/payments${query(params)}`),
  refunds: (editionId) => api(`${adminBase(editionId)}/refunds`),
  createRefund: (editionId, payload) =>
    api(`${adminBase(editionId)}/refunds`, { method: 'POST', body: payload }),
  verifications: (editionId, params = {}) =>
    api(`${adminBase(editionId)}/verifications${query(params)}`),
  verificationDocument: (editionId, verificationId) =>
    api(`${adminBase(editionId)}/verifications/${verificationId}/document`),
  decideVerification: (editionId, verificationId, payload) =>
    api(`${adminBase(editionId)}/verifications/${verificationId}/decide`, {
      method: 'POST',
      body: payload,
    }),
  registrations: (editionId, params = {}) =>
    api(`${adminBase(editionId)}/registrations${query(params)}`),
  announcements: (editionId) => api(`${adminBase(editionId)}/announcements`),
  createAnnouncement: (editionId, payload) =>
    api(`${adminBase(editionId)}/announcements`, { method: 'POST', body: payload }),
  updateAnnouncement: (editionId, announcementId, payload) =>
    api(`${adminBase(editionId)}/announcements/${announcementId}`, { method: 'PATCH', body: payload }),
  deleteAnnouncement: (editionId, announcementId) =>
    api(`${adminBase(editionId)}/announcements/${announcementId}`, { method: 'DELETE' }),
  audit: (editionId, params = {}) => api(`${adminBase(editionId)}/audit${query(params)}`),
  attendance: (editionId, params = {}) =>
    api(`${adminBase(editionId)}/attendance${query(params)}`),
  checkin: (editionId, payload) =>
    api(`${adminBase(editionId)}/checkin`, { method: 'POST', body: payload }),
  recentCheckins: (editionId) => api(`${adminBase(editionId)}/recent-checkins`),
};
