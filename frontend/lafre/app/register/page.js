'use client';

import { useState } from 'react';
import { apiFetch, redirectTo } from '../lib/api';

function ErrorBox({ message, debug }) {
  if (!message) return null;
  return <div className="auth2-alert"><p>{message}</p>{debug ? <details className="auth-debug"><summary>Debug details</summary>{debug}</details> : null}</div>;
}

export default function StudentRegister() {
  const [form, setForm] = useState({ full_name: '', institution: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [debug, setDebug] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  function update(name, value) { setForm((old) => ({ ...old, [name]: value })); setFieldErrors((old) => ({ ...old, [name]: undefined })); setError(''); setDebug(''); }
  async function submit(e) {
    e.preventDefault();
    setError(''); setDebug(''); setFieldErrors({}); setLoading(true);
    try {
      await apiFetch('/accounts/student/register/', { method: 'POST', body: JSON.stringify(form) });
      redirectTo('/pending');
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
          <div className="auth2-side-copy"><h1>A quiet desk for the study of law.</h1><p>Student accounts require admin approval before chat access.</p></div>
          <p className="auth2-side-footer">Student portal · For educational use</p>
        </aside>
        <section className="auth2-panel">
          <form className="auth2-form-card" onSubmit={submit} noValidate>
            <a className="lafre-auth-mobile-brand" href="/"><span className="brand-mark">⚖</span><strong>LAFRE</strong></a>
            <header className="auth2-form-head"><h2>Create your student account</h2><p>New accounts require admin approval before chat access.</p></header>
            <ErrorBox message={error} debug={debug} />
            <label className="auth2-field"><span>Full name</span><input value={form.full_name} onChange={(e)=>update('full_name', e.target.value)} required autoComplete="name" />{fieldErrors.full_name?.[0] ? <small className="auth2-error-text">{fieldErrors.full_name[0]}</small> : null}</label>
            <label className="auth2-field"><span>Institution (optional)</span><input value={form.institution} onChange={(e)=>update('institution', e.target.value)} placeholder="e.g. University of Lagos" />{fieldErrors.institution?.[0] ? <small className="auth2-error-text">{fieldErrors.institution[0]}</small> : null}</label>
            <label className="auth2-field"><span>Email</span><input type="email" value={form.email} onChange={(e)=>update('email', e.target.value)} required autoComplete="email" />{fieldErrors.email?.[0] ? <small className="auth2-error-text">{fieldErrors.email[0]}</small> : null}</label>
            <label className="auth2-field"><span>Password</span><input type="password" value={form.password} onChange={(e)=>update('password', e.target.value)} required autoComplete="new-password" />{fieldErrors.password?.[0] ? <small className="auth2-error-text">{fieldErrors.password[0]}</small> : null}</label>
            <button className="auth2-primary" type="submit" disabled={loading}>{loading ? 'Creating account…' : 'Create account'}</button>
            <p className="auth2-switch">Already have an account? <a href="/login">Sign in</a></p>
          </form>
        </section>
      </section>
    </main>
  );
}
