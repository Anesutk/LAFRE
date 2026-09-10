'use client';

import { useState } from 'react';
import { apiFetch, redirectTo, saveAuth } from '../lib/api';

export default function LawyerLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const result = await apiFetch('/accounts/lawyer/login/', { method: 'POST', body: JSON.stringify({ email: email.trim(), password }) });
      saveAuth(result);
      redirectTo(result.redirect_to || '/dashboards/lawyer');
    } catch (err) {
      setError(err.message || 'We could not sign you in.');
    } finally { setLoading(false); }
  }
  return (
    <main className="auth2-page">
      <section className="auth2-shell">
        <aside className="auth2-side">
          <a className="study-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
          <div className="auth2-side-copy"><h1>A professional workspace for verified legal practitioners.</h1><p>Lawyer portal accounts are issued and approved by LAFRE administrators.</p></div>
          <p className="auth2-side-footer">Lawyer portal · Verified access only</p>
        </aside>
        <section className="auth2-panel">
          <form className="auth2-form-card" onSubmit={submit} noValidate>
            <a className="lafre-auth-mobile-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
            <header className="auth2-form-head"><h2>Lawyer portal</h2><p>Sign in with the credentials issued by LAFRE Admin.</p></header>
            {error ? <div className="auth2-alert"><p>{error}</p></div> : null}
            <label className="auth2-field"><span>Email</span><input autoComplete="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
            <label className="auth2-field"><span>Password</span><input autoComplete="current-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
            <button className="auth2-primary" type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
            <p className="auth2-switch"><a href="/login">Student or civilian login</a></p>
          </form>
        </section>
      </section>
    </main>
  );
}
