'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import LafreShell from '../../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../../lib/api';
import { Icon } from '../../prototype/components/icons';
import ui from '../../prototype/components/ui.module.css';
import styles from '../../forum/forum.module.css';

export default function LawyerDetailPage() {
  const { slug } = useParams(); const profile = getProfile();
  const role = profile?.role === 'student' ? 'student' : profile?.role === 'lawyer' ? 'lawyer' : 'visitor';
  const [lawyer,setLawyer]=useState(null); const [error,setError]=useState('');
  useEffect(()=>{if(slug) apiFetch(`/forum/lawyers/${slug}/`).then(r=>setLawyer(r.lawyer)).catch(e=>setError(e.message||'Could not load this profile.'));},[slug]);
  return <LafreShell role={role} active="Find Lawyers"><div className={ui.shell}>
    <Link href="/lawyers" className={styles.backLink}><Icon name="arrow" size={14}/> Find lawyers</Link>
    {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={16}/><p>{error}</p></div>}
    {lawyer && <section className={`${ui.panel} ${ui.pad}`} style={{marginTop:14}}><div className={styles.detailMeta}><span className={styles.tag}>{lawyer.location || 'Zimbabwe'}</span>{lawyer.verified ? <span className={styles.verified}>★★★ Verified lawyer</span> : null}</div><h1 className={ui.title} style={{marginTop:12}}>{lawyer.name}</h1><p className={ui.subtitle}>{lawyer.firm_name || 'Independent practice'} · {lawyer.practice_area || 'Legal services'}</p><div className={ui.threeCol} style={{marginTop:18}}><div><b>Experience</b><p className={ui.muted}>{lawyer.years_experience || 0} years</p></div><div><b>Rating</b><p className={ui.muted}>{Number(lawyer.rating || 0).toFixed(1)} ★ · {lawyer.reviews_count || 0} reviews</p></div><div><b>Mentorship</b><p className={ui.muted}>{lawyer.mentorship_available ? 'Available' : 'Not currently offered'}</p></div></div><div className={ui.divider}/><h2 style={{fontSize:19}}>About</h2><p style={{fontSize:14,lineHeight:1.8}}>{lawyer.bio || 'No biography has been provided.'}</p><div className={ui.btnRow} style={{marginTop:18}}>{lawyer.public_email ? <a className={styles.primaryButton} href={`mailto:${lawyer.public_email}`}><Icon name="message" size={15}/> Email lawyer</a> : null}{lawyer.phone ? <a className={styles.secondaryButton} style={{width:'auto'}} href={`tel:${lawyer.phone}`}><Icon name="lawyer" size={15}/> Call</a> : null}</div></section>}
    {!lawyer && !error && <div className={`${ui.panel} ${ui.pad} ${styles.loading}`}><span className={styles.spinner}/> Loading profile…</div>}
  </div></LafreShell>;
}
