'use client';

import { useState } from 'react';
import { apiFetch, redirectTo } from '../lib/api';

function ErrorBox({ message, debug }) {
  if (!message) return null;
  return <div className="auth2-alert"><p>{message}</p>{debug ? <details className="auth-debug"><summary>Debug details</summary>{debug}</details> : null}</div>;
}

export default function CitizenRegister() {
  const [form, setForm] = useState({ full_name: '', phone: '', city: '', email: '', password: '', confirm_password: '' });
  const [error, setError] = useState('');
  const [debug, setDebug] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  function update(name, value) {
    setForm((old) => ({ ...old, [name]: value }));
    setFieldErrors((old) => ({ ...old, [name]: undefined }));
    setError('');
    setDebug('');
  }
  async function submit(e) {
    e.preventDefault();
    setError(''); setDebug(''); setFieldErrors({}); setLoading(true);
    try {
      const result = await apiFetch('/accounts/citizen/register/', { method: 'POST', body: JSON.stringify(form) });
      redirectTo(result.redirect_to || '/pending');
    } catch (err) {
      setError(err.message || 'Could not create your account.');
      setDebug(err.debug || '');
      setFieldErrors(err.fieldErrors || {});
    } finally { setLoading(false); }
  }
  return (
    <main className="auth2-page">
      <section className="auth2-shell">
        <aside className="auth2-side">
          <a className="study-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
          <div className="auth2-side-copy"><h1>Practical legal help, grounded in your situation.</h1><p>Civilian accounts require approval before private legal services become available.</p></div>
          <p className="auth2-side-footer">Civilian portal · For public legal support</p>
        </aside>
        <section className="auth2-panel">
          <form className="auth2-form-card" onSubmit={submit} noValidate>
            <a className="lafre-auth-mobile-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
            <header className="auth2-form-head"><h2>Create your civilian account</h2><p>Submit your details for administrator approval.</p></header>
            <ErrorBox message={error} debug={debug} />
            {[
              ['full_name', 'Full name', 'text', 'name'],
              ['phone', 'Phone number', 'tel', 'tel'],
              ['city', 'City or town', 'text', 'address-level2'],
              ['email', 'Email', 'email', 'email'],
              ['password', 'Password', 'password', 'new-password'],
              ['confirm_password', 'Confirm password', 'password', 'new-password'],
            ].map(([name, label, type, autoComplete]) => <label className="auth2-field" key={name}><span>{label}</span><input type={type} value={form[name]} onChange={(e) => update(name, e.target.value)} required autoComplete={autoComplete} />{fieldErrors[name]?.[0] ? <small className="auth2-error-text">{fieldErrors[name][0]}</small> : null}</label>)}
            <button className="auth2-primary" type="submit" disabled={loading}>{loading ? 'Creating account…' : 'Create account'}</button>
            <p className="auth2-switch">Already have an account? <a href="/login">Sign in</a></p>
          </form>
        </section>
      </section>
    </main>
  );
}
