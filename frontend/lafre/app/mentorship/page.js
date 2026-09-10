'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../lib/api';
import { Icon } from '../prototype/components/icons';
import ui from '../prototype/components/ui.module.css';
import styles from '../forum/forum.module.css';

function formatRole(profile) { return profile?.role === 'lawyer' ? 'lawyer' : 'student'; }

export default function Mentorship() {
  const [programmes, setProgrammes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const profile = getProfile();

  useEffect(() => {
    apiFetch('/forum/mentorship/')
      .then(r => setProgrammes(r.programmes || []))
      .catch(e => setError(e.message || 'Could not load mentorship programmes.'))
      .finally(() => setLoading(false));
  }, []);

  return <LafreShell active="Mentorship" role={formatRole(profile)}>
    <div className={ui.shell}>
      <div className={styles.eyebrow}>Private professional development</div>
      <h1 className={ui.title}>Mentorship</h1>
      <p className={ui.subtitle}>Join structured programmes led by verified lawyers. Mentorship is for career and professional development, not personal legal representation.</p>
      {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={16} /><p>{error}</p></div>}
      <div className={styles.feedHeader} style={{marginTop:24}}><div><div className={styles.eyebrow}>Available programmes</div><h2>Learn from practising professionals</h2></div><span className={styles.feedCount}>{loading ? 'Loading…' : `${programmes.length} programme${programmes.length === 1 ? '' : 's'}`}</span></div>
      {loading ? <div className={`${ui.panel} ${ui.pad} ${styles.loading}`}><span className={styles.spinner} /> Loading programmes…</div> : <div className={ui.twoCol}>
        <section className={`${ui.panel} ${ui.pad}`}>
          {!programmes.length && <div className={styles.empty}><Icon name="users" size={28}/><h3>No programmes available</h3><p>Verified lawyers can publish mentorship programmes through their professional portal.</p></div>}
          {programmes.map(p => <article className={styles.post} key={p.id} style={{marginBottom:12}}><div className={styles.postAccent}/><div className={styles.postBody}>
            <div className={styles.postMeta}><span className={styles.tag}>{p.area || 'Professional development'}</span><span>{p.weeks} weeks</span><span>·</span><span>{p.student_count || 0} students</span></div>
            <h2><Link href={`/mentorship/${p.id}`}>{p.title}</Link></h2>
            <p>{p.description}</p>
            <div className={styles.postFooter}><span><Icon name="lawyer" size={14}/> {p.lawyer_name}</span><span>{p.is_free ? 'Free' : `${p.fee_amount || ''}`}</span><Link href={`/mentorship/${p.id}`}>{p.joined ? 'Open programme' : 'View programme'} <Icon name="arrow" size={14}/></Link></div>
          </div></article>)}
        </section>
        <aside className={`${ui.panel} ${ui.pad}`}>
          <div className={styles.eyebrow}>How it works</div>
          {['Choose a programme that matches your goals','Open the programme and review its topics','Join to unlock the private group','Use group messages and materials to learn with your cohort'].map((x,i)=><div className={ui.listItem} key={x}><div className={ui.row}><span className={styles.avatar}>{i+1}</span><span style={{fontSize:12,lineHeight:1.45}}>{x}</span></div></div>)}
        </aside>
      </div>}
    </div>
  </LafreShell>;
}
