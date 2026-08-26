'use client';

import { useState } from 'react';
import { apiFetch, saveAuth, redirectTo } from '../lib/api';

function ErrorBox({ message, debug }) {
  if (!message) return null;
  return <div className="auth2-alert"><p>{message}</p>{debug ? <details className="auth-debug"><summary>Debug details</summary>{debug}</details> : null}</div>;
}

export default function StudentLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [debug, setDebug] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(''); setDebug(''); setFieldErrors({}); setLoading(true);
    try {
      const res = await apiFetch('/accounts/login/', { method: 'POST', body: JSON.stringify({ email: email.trim(), password }) });
      saveAuth(res);
      redirectTo(res.redirect_to || '/chat');
    } catch (err) {
      setError(err.message || 'We could not sign you in.');
      setDebug(err.debug || '');
      setFieldErrors(err.fieldErrors || {});
    } finally { setLoading(false); }
  }

  return (
    <main className="auth2-page">
      <section className="auth2-shell">
        <aside className="auth2-side">
          <a className="study-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
          <div className="auth2-side-copy"><h1>"The life of the law has not been logic; it has been experience."</h1><p>— Oliver Wendell Holmes Jr.</p></div>
          <p className="auth2-side-footer">Student portal · For educational use</p>
        </aside>
        <section className="auth2-panel">
          <form className="auth2-form-card" onSubmit={submit} noValidate>
            <a className="lafre-auth-mobile-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
            <header className="auth2-form-head"><h2>Welcome back</h2><p>Sign in to your LAFRE student workspace.</p></header>
            <ErrorBox message={error} debug={debug} />
            <label className="auth2-field"><span>Email</span><input autoComplete="email" type="email" value={email} onChange={(e)=>setEmail(e.target.value)} required />{fieldErrors.email?.[0] ? <small className="auth2-error-text">{fieldErrors.email[0]}</small> : null}</label>
            <label className="auth2-field"><span>Password</span><input autoComplete="current-password" type="password" value={password} onChange={(e)=>setPassword(e.target.value)} required />{fieldErrors.password?.[0] || fieldErrors.non_field_errors?.[0] ? <small className="auth2-error-text">{fieldErrors.password?.[0] || fieldErrors.non_field_errors?.[0]}</small> : null}</label>
            <button className="auth2-primary" type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
            <p className="auth2-switch">New here? <a href="/register">Create an account</a></p>
          </form>
        </section>
      </section>
    </main>
  );
}
