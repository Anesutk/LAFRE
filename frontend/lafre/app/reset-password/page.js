'use client';
import { useState } from 'react';
import { apiFetch } from '../lib/api';

export default function ResetPassword() {
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);
  const token = typeof window !== 'undefined' ? new URLSearchParams(location.search).get('token') : '';

  async function submit(e) {
    e.preventDefault();
    setErr(''); setMsg(''); setLoading(true);
    try {
      const r = await apiFetch('/accounts/password-reset/confirm/', { method: 'POST', body: JSON.stringify({ token, password }) });
      setMsg(r.message || 'Password updated. You can now sign in.');
    } catch (error) {
      setErr(error.message || 'Could not reset password.');
    } finally { setLoading(false); }
  }

  return (
    <main className="lafre-auth-single">
      <a className="lafre-wordmark" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
      <div className="centered" style={{ textAlign: 'left' }}>
        <div className="auth-form-head">
          <h2>Choose new password</h2>
          <p>Pick a strong password for your account.</p>
        </div>
        {msg && <div className="alert-success">{msg} <a href="/login" style={{ color: 'var(--green)', fontWeight: 600 }}>Sign in →</a></div>}
        {err && <div className="alert-error">{err}</div>}
        {!msg && (
          <form onSubmit={submit} style={{ display: 'grid', gap: '.875rem' }}>
            <label className="auth2-field">
              <span>New password</span>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="new-password" />
            </label>
            <button className="auth2-primary" type="submit" disabled={loading || !password}>
              {loading ? 'Saving…' : 'Set new password'}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
