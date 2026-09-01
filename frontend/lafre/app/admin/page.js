'use client';
import { useEffect, useState, useCallback } from 'react';
import { apiFetch, getProfile, redirectTo, saveAuth } from '../lib/api';

function StatCard({ label, value }) {
  return <div className="admin-stat"><b>{value ?? '—'}</b><span>{label}</span></div>;
}

function StatusBadge({ status }) {
  return <span className={`admin-badge admin-badge-${status}`}>{status}</span>;
}

function PasswordPrompt({ title, onConfirm, onCancel }) {
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const submit = async () => {
    setBusy(true); setError('');
    try { await onConfirm(password); } catch (err) { setError(err.message || 'Action failed.'); } finally { setBusy(false); }
  };
  return <div className="admin-modal-backdrop" onClick={onCancel}>
    <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
      <h3>{title}</h3>
      <p>Confirm your admin password to continue — this action changes account access.</p>
      <input type="password" placeholder="Your password" value={password} onChange={(e) => setPassword(e.target.value)} autoFocus />
      {error ? <p className="admin-modal-error">{error}</p> : null}
      <div className="admin-modal-actions">
        <button type="button" className="admin-btn-ghost" onClick={onCancel} disabled={busy}>Cancel</button>
        <button type="button" className="admin-btn-solid" onClick={submit} disabled={busy || !password}>{busy ? 'Confirming…' : 'Confirm'}</button>
      </div>
    </div>
  </div>;
}

export default function AdminPage() {
  const [mounted, setMounted] = useState(false);
  const [profile, setProfile] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [roleFilter, setRoleFilter] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [pendingAction, setPendingAction] = useState(null); // { type: 'approve'|'save', userId, payload }
  const [selected, setSelected] = useState(null);
  const [notice, setNotice] = useState('');

  const loadDashboard = useCallback(async () => {
    try { setDashboard(await apiFetch('/accounts/admin/dashboard/')); } catch { /* ignore, shown via users list regardless */ }
  }, []);

  const loadUsers = useCallback(async () => {
    const params = new URLSearchParams();
    if (statusFilter) params.set('status', statusFilter);
    if (roleFilter) params.set('role', roleFilter);
    if (query.trim()) params.set('q', query.trim());
    try {
      const res = await apiFetch(`/accounts/admin/users/?${params.toString()}`);
      setUsers(res.users || []);
    } catch (err) {
      setNotice(err.message || 'Could not load users.');
    }
  }, [statusFilter, roleFilter, query]);

  useEffect(() => {
    setMounted(true);
    const cached = getProfile();
    if (!cached) { redirectTo('/login'); return; }
    setProfile(cached); // show something immediately while the fresh check runs
    // Never trust the cached profile alone for an admin gate - it's whatever was true at
    // last login, and can go stale the moment someone's is_superuser flag changes without
    // them logging out and back in. Always re-check against the live account first.
    apiFetch('/accounts/me/').then((res) => {
      const fresh = res.profile;
      setProfile(fresh);
      saveAuth({ profile: fresh }); // keep the cached copy in sync so the rest of the app sees it too
      if (fresh?.is_superuser) {
        Promise.all([loadDashboard(), loadUsers()]).finally(() => setLoading(false));
      } else {
        setLoading(false);
      }
    }).catch(() => {
      // Session may have expired - fall back to the cached value rather than hard-failing,
      // the render below still gates correctly either way.
      setLoading(false);
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (mounted && profile?.is_superuser) loadUsers();
  }, [statusFilter, roleFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const quickApprove = (user) => setPendingAction({ type: 'approve', userId: user.id, label: user.full_name || user.email });

  const runApprove = async (password) => {
    await apiFetch(`/accounts/admin/users/${pendingAction.userId}/quick-approve/`, { method: 'POST', body: JSON.stringify({ password }) });
    setPendingAction(null);
    setNotice('Account approved.');
    await Promise.all([loadDashboard(), loadUsers()]);
  };

  if (!mounted) return null;

  if (!profile?.is_superuser) {
    return <main className="admin-denied">
      <div className="admin-denied-card">
        <span className="admin-denied-icon">⚖</span>
        <h1>Admin access only</h1>
        <p>This area is restricted to super accounts. If you believe this is a mistake, contact whoever manages your LAFRE deployment.</p>
        <a className="admin-btn-solid" href="/chat">Back to chat</a>
      </div>
    </main>;
  }

  return <main className="admin-shell">
    <header className="admin-header">
      <div className="admin-brand"><span className="admin-mark">⚖</span> LAFRE Admin</div>
      <a href="/chat" className="admin-btn-ghost">← Back to app</a>
    </header>

    {notice ? <div className="admin-notice" onClick={() => setNotice('')}>{notice}</div> : null}

    <section className="admin-stats">
      <StatCard label="Pending students" value={dashboard?.stats?.pending_students} />
      <StatCard label="Pending citizens" value={dashboard?.stats?.pending_citizens} />
      <StatCard label="Approved students" value={dashboard?.stats?.approved_students} />
      <StatCard label="Approved citizens" value={dashboard?.stats?.approved_citizens} />
      <StatCard label="Lawyers" value={dashboard?.stats?.lawyers} />
      <StatCard label="Suspended" value={dashboard?.stats?.suspended_users} />
    </section>

    {dashboard?.today_queue?.length ? <section className="admin-queue">
      <h2>Awaiting approval</h2>
      <div className="admin-queue-list">
        {dashboard.today_queue.map((item) => <div className="admin-queue-row" key={item.user_id}>
          <div><b>{item.name}</b><span>{item.email} · {item.title}</span></div>
          <button type="button" className="admin-btn-solid admin-btn-sm" onClick={() => quickApprove({ id: item.user_id, full_name: item.name, email: item.email })}>Approve</button>
        </div>)}
      </div>
    </section> : null}

    <section className="admin-directory">
      <div className="admin-directory-head">
        <h2>All accounts</h2>
        <div className="admin-filters">
          <input placeholder="Search name or email…" value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && loadUsers()} />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="suspended">Suspended</option>
          </select>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">All roles</option>
            <option value="student">Student</option>
            <option value="citizen">Citizen</option>
            <option value="lawyer">Lawyer</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>

      {loading ? <p className="admin-loading">Loading accounts…</p> : (
        <table className="admin-table">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th></th></tr></thead>
          <tbody>
            {users.map((u) => <tr key={u.id} onClick={() => setSelected(u)} className={selected?.id === u.id ? 'active' : ''}>
              <td>{u.full_name}</td>
              <td>{u.email}</td>
              <td>{u.role}</td>
              <td><StatusBadge status={u.status} /></td>
              <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
              <td>{u.status === 'pending' ? <button type="button" className="admin-btn-ghost admin-btn-sm" onClick={(e) => { e.stopPropagation(); quickApprove(u); }}>Approve</button> : null}</td>
            </tr>)}
            {!users.length ? <tr><td colSpan={6} className="admin-empty">No accounts match this filter.</td></tr> : null}
          </tbody>
        </table>
      )}
    </section>

    {selected ? <aside className="admin-drawer">
      <div className="admin-drawer-head"><h3>{selected.full_name}</h3><button type="button" onClick={() => setSelected(null)}>×</button></div>
      <dl>
        <dt>Email</dt><dd>{selected.email}</dd>
        <dt>Role</dt><dd>{selected.role} (requested: {selected.requested_role})</dd>
        <dt>Status</dt><dd><StatusBadge status={selected.status} /></dd>
        <dt>Institution</dt><dd>{selected.institution || '—'}</dd>
        <dt>Daily message limit</dt><dd>{selected.daily_message_limit ?? 'Unlimited'}</dd>
        <dt>Messages used today</dt><dd>{selected.messages_used_today ?? 0}</dd>
      </dl>
      {selected.status === 'pending' ? <button type="button" className="admin-btn-solid" style={{ width: '100%' }} onClick={() => quickApprove(selected)}>Approve this account</button> : null}
    </aside> : null}

    {pendingAction?.type === 'approve' ? <PasswordPrompt title={`Approve ${pendingAction.label}?`} onConfirm={runApprove} onCancel={() => setPendingAction(null)} /> : null}
  </main>;
}
