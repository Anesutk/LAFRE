'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import { apiFetch, clearAuth } from '../lib/api';
import { Icon } from '../prototype/components/icons';
import ui from '../prototype/components/ui.module.css';
import styles from '../forum/forum.module.css';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { apiFetch('/accounts/me/').then(r => setProfile(r.profile || r)).catch(e => setError(e.message || 'Could not load your profile.')); }, []);
  function logout() { clearAuth(); window.location.href = '/login'; }
  const role = profile?.role === 'student' ? 'student' : profile?.role === 'lawyer' ? 'lawyer' : profile?.role === 'citizen' ? 'civilian' : 'visitor';
  return <LafreShell role={role} active="Home"><div className={ui.shell}>
    <div className={styles.eyebrow}>Account</div><h1 className={ui.title}>Your profile.</h1><p className={ui.subtitle}>This page shows the account data currently stored by LAFRE.</p>
    {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={16}/><p>{error}</p></div>}
    <section className={`${ui.panel} ${ui.pad}`} style={{maxWidth:820,marginTop:18}}>
      <div className={ui.row} style={{justifyContent:'flex-start'}}><div className={styles.avatarLarge}><Icon name="user" size={18}/></div><div><h2 style={{margin:0,fontSize:21}}>{profile?.full_name || 'Loading…'}</h2><div className={ui.muted} style={{fontSize:12}}>{profile?.role || 'account'} · {profile?.status || '—'}</div></div></div>
      <div className={ui.divider}/><dl style={{display:'grid',gridTemplateColumns:'160px 1fr',gap:'10px 18px',fontSize:13,margin:0}}>{[['Email',profile?.email],['Institution',profile?.institution || '—'],['Student number',profile?.student_number || '—'],['City',profile?.city || '—'],['Phone',profile?.phone || '—'],['Account status',profile?.status || '—']].map(([k,v])=><div key={k} style={{display:'contents'}}><dt className={ui.muted}>{k}</dt><dd style={{margin:0,fontWeight:700}}>{v || '—'}</dd></div>)}</dl>
      <div className={ui.btnRow} style={{marginTop:20}}><Link href={role === 'student' ? '/settings' : '/settings'} className={styles.secondaryButton}>Open settings</Link><button className={styles.primaryButton} onClick={logout}><Icon name="logout" size={15}/> Sign out</button></div>
    </section>
  </div></LafreShell>;
}
