'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import { apiFetch } from '../lib/api';
import ui from '../prototype/components/ui.module.css';

export default function LawyersPage() {
  const [lawyers, setLawyers] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { apiFetch('/forum/lawyers/').then((result) => setLawyers(result.lawyers || [])).catch((err) => setError(err.message || 'Could not load lawyers.')); }, []);
  return <LafreShell active="Find Lawyers"><div className={ui.shell}>
    <div className={ui.eyebrow}>Verified professionals</div><h1 className={ui.title}>Find a lawyer.</h1><p className={ui.subtitle}>Browse real lawyer profiles provided by the LAFRE backend.</p>
    {error && <div className={ui.panel + ' ' + ui.pad}><p>{error}</p></div>}
    <div className={ui.threeCol}>{lawyers.map((lawyer) => <article className={ui.panel + ' ' + ui.pad} key={lawyer.slug}><div className={ui.eyebrow}>{lawyer.location || 'Location not listed'}</div><h2 style={{ fontSize: 20 }}>{lawyer.full_name || lawyer.name}</h2><p className={ui.muted}>{lawyer.practice_area || 'Legal services'} · {lawyer.years_experience || 0} years</p><p>{lawyer.bio || 'Professional profile information is available from this lawyer.'}</p><Link href={`/lawyers/${lawyer.slug}`} className={ui.outlineBtn}>View profile</Link></article>)}{!lawyers.length && !error && <p className={ui.muted}>No lawyer profiles are available yet.</p>}</div>
  </div></LafreShell>;
}
