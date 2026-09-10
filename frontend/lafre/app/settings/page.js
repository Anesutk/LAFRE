'use client';

import { useEffect, useState } from 'react';
import StudentShell from '../components/StudentShell';
import { apiFetch, checkBackendConnection, clearApiBaseOverride, getApiBase, getProfile } from '../lib/api';

export default function StudentSettings() {
  const [profile, setProfile] = useState(null);
  const [connection, setConnection] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { document.title = 'Settings - LAFRE'; setProfile(getProfile()); apiFetch('/accounts/me/').then(r => setProfile(r.profile || r)).catch(e => setError(e.message || 'Could not load account settings.')); }, []);
  async function testConnection() { setConnection(await checkBackendConnection()); }
  function resetApi() { clearApiBaseOverride(); setConnection(null); }
  return <StudentShell active="settings" title="Settings">
    <section className="warm-page-copy"><a href="/chat" className="warm-back">← Back to chat</a><h1>Settings</h1><p>Account and connection information for your LAFRE student workspace.</p></section>
    {error ? <div className="error-strip">{error}</div> : null}
    <section className="warm-account-card"><h2>Account</h2><dl><dt>Name</dt><dd>{profile?.full_name || 'Loading…'}</dd><dt>Email</dt><dd>{profile?.email || '—'}</dd><dt>Institution</dt><dd>{profile?.institution || 'Midlands State University'}</dd><dt>Status</dt><dd>{profile?.status || '—'}</dd></dl></section>
    <section className="warm-empty-card"><h2>Backend connection</h2><p>Current API base: <code>{getApiBase()}</code></p><div style={{display:'flex',gap:8,flexWrap:'wrap'}}><button type="button" onClick={testConnection}>Test connection</button><button type="button" onClick={resetApi}>Use default API address</button></div>{connection ? <p style={{marginBottom:0,marginTop:12}}>{connection.reachable ? `Backend responded with HTTP ${connection.status}.` : `Backend is not reachable: ${connection.debug || 'network error'}`}</p> : null}</section>
  </StudentShell>;
}
