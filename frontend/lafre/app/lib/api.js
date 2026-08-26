const API_OVERRIDE_KEY = 'lafre_api_base_override';

// Lets the app point at a custom backend host at runtime (e.g. a tunnel URL,
// a staging server, or a different port) without needing a rebuild/redeploy.
// Set from the Settings page. Falls back to NEXT_PUBLIC_API_BASE_URL, then to
// sensible localhost/relative defaults.
export function getApiBaseOverride() {
  if (typeof window === 'undefined') return '';
  try { return localStorage.getItem(API_OVERRIDE_KEY) || ''; } catch { return ''; }
}

export function setApiBaseOverride(url) {
  if (typeof window === 'undefined') return;
  try {
    if (url && url.trim()) localStorage.setItem(API_OVERRIDE_KEY, url.trim().replace(/\/$/, ''));
    else localStorage.removeItem(API_OVERRIDE_KEY);
  } catch { /* ignore storage errors (e.g. private mode) */ }
}

export function clearApiBaseOverride() { setApiBaseOverride(''); }

export function getApiBase() {
  const override = getApiBaseOverride();
  if (override) return override.replace(/\/$/, '');

  const env = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env) return env.replace(/\/$/, '');

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `${protocol}//${hostname}:8000/api`;
    }
    // No env var and not on localhost: assume the backend is reverse-proxied
    // on the same origin (e.g. /api). Once a real backend host is known,
    // set NEXT_PUBLIC_API_BASE_URL at build time or use the Settings page
    // to override it at runtime.
    return '/api';
  }
  return 'http://localhost:8000/api';
}

export const API_BASE = getApiBase();

// Quick reachability check used by the Settings page's "Test connection"
// button. Distinguishes "server unreachable" (network/DNS/CORS failure)
// from "server reachable but returned an error", which is useful while a
// backend is still being wired up.
export async function checkBackendConnection() {
  const base = getApiBase();
  try {
    const res = await fetch(base, { method: 'GET', mode: 'cors', cache: 'no-store' });
    return { ok: true, reachable: true, status: res.status, base };
  } catch (error) {
    return { ok: false, reachable: false, status: 0, base, debug: String(error?.message || error) };
  }
}

export class ApiError extends Error {
  constructor(message, { status = 0, payload = null, fieldErrors = {}, debug = '' } = {}) {
    super(message || 'Request failed.');
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
    this.fieldErrors = fieldErrors;
    this.debug = debug;
  }
}

export function getToken() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('lafre_token') || '';
}

export function getSessionId() {
  if (typeof window === 'undefined') return '';
  const key = 'lafre_guest_session';
  try {
    let value = localStorage.getItem(key);
    if (!value) {
      value = crypto.randomUUID();
      localStorage.setItem(key, value);
    }
    return value;
  } catch { return ''; }
}

export function getProfile() {
  if (typeof window === 'undefined') return null;
  try { return JSON.parse(localStorage.getItem('lafre_profile') || 'null'); } catch { return null; }
}

export function saveAuth(payload) {
  if (typeof window === 'undefined') return;
  if (payload?.token) localStorage.setItem('lafre_token', payload.token);
  if (payload?.profile) localStorage.setItem('lafre_profile', JSON.stringify(payload.profile));
}

export function clearAuth() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('lafre_token');
  localStorage.removeItem('lafre_profile');
}

function toArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.map(String);
  if (typeof value === 'object') return Object.values(value).flatMap(toArray);
  return [String(value)];
}

function extractFieldErrors(data) {
  if (!data || typeof data !== 'object') return {};
  const source = data.errors || data;
  if (!source || typeof source !== 'object') return {};
  const output = {};
  for (const [key, value] of Object.entries(source)) {
    if (['ok', 'success', 'message', 'detail', 'debug', 'debug_detail', 'traceback', 'redirect_to', 'profile', 'token'].includes(key)) continue;
    output[key] = toArray(value);
  }
  return output;
}

function extractDebug(data) {
  if (!data) return '';
  if (typeof data === 'object') {
    return String(data.debug || data.debug_detail || data.traceback || data.exception || '').slice(0, 2500);
  }
  if (typeof data === 'string') return cleanHtmlError(data, true);
  return '';
}

function extractMessage(data) {
  if (!data) return '';
  if (typeof data === 'string') return cleanHtmlError(data, false);
  if (typeof data.message === 'string') return data.message;
  if (typeof data.detail === 'string') return data.detail;
  const fieldErrors = extractFieldErrors(data);
  const first = Object.values(fieldErrors).flat()[0];
  return first || 'Request failed. Please try again.';
}

function cleanHtmlError(text, debugMode = false) {
  if (!text) return debugMode ? '' : 'The server returned an error. Please try again.';
  const stripped = String(text)
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!stripped) return debugMode ? '' : 'The server returned an error. Please try again.';
  if (debugMode) return stripped.slice(0, 2500);
  const lower = stripped.toLowerCase();
  if (lower.includes('traceback') || lower.includes('exception location') || lower.includes('django')) {
    return 'The backend returned an internal error. Open details below to see the debug message.';
  }
  return stripped.slice(0, 700);
}

export async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const sessionId = getSessionId();
  if (sessionId) headers['X-Session-ID'] = sessionId;
  const hasBody = Object.prototype.hasOwnProperty.call(options, 'body');
  if (hasBody && !(options.body instanceof FormData) && !headers['Content-Type']) headers['Content-Type'] = 'application/json';

  const base = getApiBase();
  let res;
  try {
    res = await fetch(`${base}${path}`, { ...options, headers });
  } catch (error) {
    throw new ApiError(
      `Could not reach the backend at ${base}. It may be offline, still starting up, or the address may be wrong. If you're running the backend locally, make sure it's started on that host/port. You can change the backend address from Settings.`,
      { debug: String(error?.message || error) }
    );
  }

  const type = res.headers.get('content-type') || '';
  const data = type.includes('application/json') ? await res.json().catch(() => ({})) : await res.text().catch(() => '');

  if (!res.ok) {
    // A 401 means the token is dead (expired, revoked, or a stale/demo profile leftover in
    // localStorage from a previous session on this browser). Clear it immediately so the UI
    // falls back to guest mode instead of continuing to show a signed-in-looking account
    // shell (email, usage, logout) for a session that isn't actually authenticated anymore.
    if (res.status === 401) {
      clearAuth();
    }
    throw new ApiError(extractMessage(data), {
      status: res.status,
      payload: data,
      fieldErrors: extractFieldErrors(data),
      debug: extractDebug(data),
    });
  }
  return data;
}

export function cleanUrl(apiPath) {
  if (!apiPath) return '#';
  if (apiPath.startsWith('http')) return apiPath;
  return `${getApiBase().replace(/\/api$/, '')}${apiPath}`;
}

export function redirectTo(path) {
  if (typeof window !== 'undefined') window.location.href = path;
}
