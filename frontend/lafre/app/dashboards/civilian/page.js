'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../../prototype/components/LafreShell';
import { apiFetch, getProfile, redirectTo } from '../../lib/api';
import ui from '../../prototype/components/ui.module.css';

export default function CivilianDashboard() {
  const [profile, setProfile] = useState(null);
  const [matters, setMatters] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const current = getProfile();
    if (!current || (current.role !== 'citizen' && !current.can_use_civilian)) {
      redirectTo('/login');
      return;
    }
    setProfile(current);
    apiFetch('/civilian/citizen/matters/')
      .then((result) => setMatters(result.matters || []))
      .catch((err) => setError(err.message || 'Could not load your matters.'));
  }, []);

  return <LafreShell role="civilian" active="Home"><div className={ui.shell}>
    <div className={ui.eyebrow}>Signed in · {profile?.full_name || profile?.email || 'Citizen'}</div>
    <h1 className={ui.title}>Your legal workspace.</h1>
    <p className={ui.subtitle}>Review your real matters, documents, and requests for professional help.</p>
    {error && <div className={ui.panel + ' ' + ui.pad}><p>{error}</p></div>}
    <div className={ui.threeCol} style={{ marginTop: 20 }}>
      <div className={ui.panel + ' ' + ui.pad}><div className={ui.eyebrow}>Matters</div><h2 style={{ fontSize: 26, margin: '6px 0' }}>{matters.length}</h2><p className={ui.muted}>Saved legal matters</p></div>
      <Link href="/legal-help" className={ui.panel + ' ' + ui.pad} style={{ textDecoration: 'none', color: '#111' }}><div className={ui.eyebrow}>Need help?</div><h3>Find a lawyer</h3><p className={ui.muted}>Submit a real request for professional assistance.</p></Link>
      <Link href="/forum" className={ui.panel + ' ' + ui.pad} style={{ textDecoration: 'none', color: '#111' }}><div className={ui.eyebrow}>Community</div><h3>Open the forum</h3><p className={ui.muted}>Read and participate in legal discussions.</p></Link>
    </div>
    <section className={ui.panel + ' ' + ui.pad} style={{ marginTop: 22 }}><div className={ui.row}><h2 style={{ fontSize: 19, margin: 0 }}>Recent matters</h2><Link href="/legal-help" className={ui.goldText}>Create matter →</Link></div>{matters.slice(0, 5).map((matter) => <div className={ui.listItem} key={matter.id}><b>{matter.title}</b><span className={ui.muted}>{matter.status} · {matter.matter_type}</span></div>)}{!matters.length && !error && <p className={ui.muted}>No matters have been created yet.</p>}</section>
  </div></LafreShell>;
}
