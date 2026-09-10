'use client';

import { useState } from 'react';
import { apiFetch, redirectTo, saveAuth } from '../lib/api';

export default function CitizenLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const result = await apiFetch('/accounts/citizen/login/', { method: 'POST', body: JSON.stringify({ email: email.trim(), password }) });
      saveAuth(result);
      redirectTo(result.redirect_to || '/dashboards/civilian');
    } catch (err) {
      setError(err.message || 'We could not sign you in.');
    } finally { setLoading(false); }
  }
  return (
    <main className="auth2-page">
      <section className="auth2-shell">
        <aside className="auth2-side">
          <a className="study-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
          <div className="auth2-side-copy"><h1>Clearer next steps for real legal situations.</h1><p>Sign in to manage your matters, documents, and requests for help.</p></div>
          <p className="auth2-side-footer">Civilian portal · Public legal support</p>
        </aside>
        <section className="auth2-panel">
          <form className="auth2-form-card" onSubmit={submit} noValidate>
            <a className="lafre-auth-mobile-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
            <header className="auth2-form-head"><h2>Civilian login</h2><p>Sign in to your LAFRE legal workspace.</p></header>
            {error ? <div className="auth2-alert"><p>{error}</p></div> : null}
            <label className="auth2-field"><span>Email</span><input autoComplete="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
            <label className="auth2-field"><span>Password</span><input autoComplete="current-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
            <button className="auth2-primary" type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
            <p className="auth2-switch">Need an account? <a href="/citizen-register">Create one</a></p>
            <p className="auth2-switch"><a href="/login">Student login</a> · <a href="/lawyer-login">Lawyer login</a></p>
          </form>
        </section>
      </section>
    </main>
  );
}
