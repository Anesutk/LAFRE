'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../../prototype/components/LafreShell';
import { apiFetch, getProfile, redirectTo } from '../../lib/api';
import ui from '../../prototype/components/ui.module.css';

export default function LawyerDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const profile = getProfile();
    if (!profile || (profile.role !== 'lawyer' && !profile.can_access_lawyer_portal)) {
      redirectTo('/login');
      return;
    }
    apiFetch('/civilian/lawyer/dashboard/')
      .then(setData)
      .catch((err) => setError(err.message || 'Could not load your lawyer dashboard.'));
  }, []);

  const lawyer = data?.lawyer;
  const reviews = data?.reviews || [];
  return <LafreShell role="lawyer" active="Home"><div className={ui.shell}>
    <div className={ui.eyebrow}>Signed in · Practising lawyer</div>
    <h1 className={ui.title}>{lawyer?.full_name || 'Professional dashboard.'}</h1>
    <p className={ui.subtitle}>Manage the document reviews assigned to your verified lawyer account.</p>
    {error && <div className={ui.panel + ' ' + ui.pad}><p>{error}</p></div>}
    <div className={ui.threeCol} style={{ marginTop: 20 }}>
      <div className={ui.panel + ' ' + ui.pad}><div className={ui.eyebrow}>Assigned reviews</div><h2 style={{ fontSize: 26, margin: '6px 0' }}>{reviews.length}</h2><p className={ui.muted}>Current review queue</p></div>
      <Link href="/lawyers" className={ui.panel + ' ' + ui.pad} style={{ textDecoration: 'none', color: '#111' }}><div className={ui.eyebrow}>Profile</div><h3>{lawyer?.verified ? 'Verified profile' : 'Profile pending verification'}</h3><p className={ui.muted}>{(lawyer?.badges || []).join(', ') || 'No badges yet'}</p></Link>
      <Link href="/forum" className={ui.panel + ' ' + ui.pad} style={{ textDecoration: 'none', color: '#111' }}><div className={ui.eyebrow}>Community</div><h3>Join the forum</h3><p className={ui.muted}>Answer permitted questions and build professional engagement.</p></Link>
    </div>
    <section className={ui.panel + ' ' + ui.pad} style={{ marginTop: 22 }}><h2 style={{ fontSize: 19, marginTop: 0 }}>Review queue</h2>{reviews.map((review) => <div className={ui.listItem} key={review.id}><b>{review.document?.title || `Review #${review.id}`}</b><span className={ui.muted}>{review.status} · {review.review_type}</span></div>)}{!reviews.length && !error && <p className={ui.muted}>No assigned reviews yet.</p>}</section>
  </div></LafreShell>;
}
