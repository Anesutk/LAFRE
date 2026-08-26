'use client';
import { useEffect, useState } from 'react';
import StudentShell from '../components/StudentShell';
import { apiFetch, getProfile } from '../lib/api';

export default function StudentUsage() {
  const [profile, setProfile] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  useEffect(() => { setProfile(getProfile()); }, []);
  async function requestMore() {
    setError(null); setMessage('');
    try { const res = await apiFetch('/students/access-request/', { method: 'POST', body: JSON.stringify({ request_type: 'messages', amount: 50 }) }); setMessage(res.message || 'Request sent to admin.'); }
    catch (err) { setError(err); }
  }
  const total = profile?.daily_message_limit || 50;
  const remaining = profile?.remaining_messages ?? profile?.remaining_daily_messages ?? total;
  const used = Math.max(0, total - remaining);
  const pct = total ? Math.min(100, Math.round((used / total) * 100)) : 0;
  return <StudentShell active="usage" title="Usage & messages">
    <section className="warm-page-copy"><a href="/chat" className="warm-back">← Back to chat</a><h1>Usage & messages</h1><p>Track your message allowance and request more if needed.</p></section>
    {message ? <div className="success-strip">✓ {message}</div> : null}{error ? <div className="error-strip">{error.message || 'Could not submit request.'}{error.debug ? <details className="auth-debug"><summary>Debug details</summary>{error.debug}</details> : null}</div> : null}
    <section className="warm-usage-card"><div className="warm-card-head"><span>◌</span><div><h2>Messages this period</h2><p>Resets monthly</p></div></div><div className="warm-usage-stat"><b>{used} / {total}</b><span>{pct}% used</span></div><div className="warm-progress"><i style={{ width: `${pct}%` }} /></div><button type="button" onClick={requestMore}>Request more messages</button></section>
    <section className="warm-account-card"><h2>Account</h2><dl><dt>Name</dt><dd>{profile?.full_name || 'Demo Student'}</dd><dt>Email</dt><dd>{profile?.email || 'student@lafre.demo'}</dd><dt>Institution</dt><dd>{profile?.institution || 'LAFRE Law School'}</dd><dt>Status</dt><dd>{profile?.status || 'Approved'}</dd></dl></section>
  </StudentShell>;
}
