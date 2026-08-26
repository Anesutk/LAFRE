'use client';
import { useState } from 'react';
import { apiFetch } from '../lib/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setErr(''); setMsg(''); setLoading(true);
    try {
      const r = await apiFetch('/accounts/password-reset/request/', { method: 'POST', body: JSON.stringify({ email }) });
      setMsg(r.message || r.debug_reset_link || 'If that email exists, a reset link has been sent.');
    } catch (error) {
      setErr(error.message || 'Could not send reset link.');
    } finally { setLoading(false); }
  }

  return (
    <main className="lafre-auth-single">
      <a className="lafre-wordmark" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
      <div className="centered" style={{ textAlign: 'left' }}>
        <div className="auth-form-head">
          <h2>Reset password</h2>
          <p>Enter your email and we'll send a reset link.</p>
        </div>
        {msg && <div className="alert-success">{msg}</div>}
        {err && <div className="alert-error">{err}</div>}
        <form onSubmit={submit} style={{ display: 'grid', gap: '.875rem' }}>
          <label className="auth2-field">
            <span>Email address</span>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" />
          </label>
          <button className="auth2-primary" type="submit" disabled={loading || !email}>
            {loading ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
        <p className="auth2-switch" style={{ marginTop: '1.25rem' }}>
          <a href="/login">← Back to sign in</a>
        </p>
      </div>
    </main>
  );
}
