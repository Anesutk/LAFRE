'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../lib/api';
import { Icon } from '../prototype/components/icons';
import ui from '../prototype/components/ui.module.css';
import styles from '../forum/forum.module.css';

export default function LawyersPage() {
  const profile = getProfile();
  const role = profile?.role === 'student' ? 'student' : profile?.role === 'lawyer' ? 'lawyer' : 'visitor';
  const [lawyers, setLawyers] = useState([]); const [query, setQuery] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  useEffect(() => { apiFetch('/forum/lawyers/').then(r => setLawyers(r.lawyers || [])).catch(e => setError(e.message || 'Could not load lawyers.')).finally(() => setLoading(false)); }, []);
  const filtered = lawyers.filter(l => [l.name,l.firm_name,l.practice_area,l.location].join(' ').toLowerCase().includes(query.toLowerCase()));
  return <LafreShell role={role} active="Find Lawyers"><div className={ui.shell}>
    <div className={styles.eyebrow}>Verified professionals</div><h1 className={ui.title}>Find a lawyer.</h1><p className={ui.subtitle}>Browse lawyer profiles added and verified through LAFRE's professional administration.</p>
    <div className={styles.searchRow}><Icon name="search" size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search by name, firm, practice area or location…"/></div>
    {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={16}/><p>{error}</p></div>}
    {loading ? <div className={`${ui.panel} ${ui.pad} ${styles.loading}`}><span className={styles.spinner}/> Loading lawyers…</div> : <div className={ui.threeCol}>{filtered.map(lawyer => <article className={`${ui.panel} ${ui.pad}`} key={lawyer.slug}><div className={styles.rowBetween}><span className={styles.tag}>{lawyer.location || 'Zimbabwe'}</span>{lawyer.verified ? <span className={styles.verified}>★★★ Verified</span> : null}</div><h2 style={{fontSize:20,margin:'12px 0 5px'}}>{lawyer.name}</h2><p className={ui.muted}>{lawyer.firm_name || 'Independent practice'} · {lawyer.practice_area || 'Legal services'}</p><p style={{fontSize:13,lineHeight:1.6}}>{lawyer.bio || 'Professional profile available from this lawyer.'}</p><div className={styles.postFooter}><span>{Number(lawyer.rating || 0).toFixed(1)} ★ · {lawyer.reviews_count || 0} reviews</span><Link href={`/lawyers/${lawyer.slug}`} className={styles.primaryButton}>View profile <Icon name="arrow" size={13}/></Link></div></article>)}</div>}
    {!loading && !filtered.length && !error && <div className={`${ui.panel} ${styles.empty}`}><Icon name="lawyer" size={28}/><h3>No matching lawyers</h3><p>Try a different name, practice area, firm or location.</p></div>}
  </div></LafreShell>;
}
