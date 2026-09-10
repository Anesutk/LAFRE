'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../../lib/api';
import { Icon } from '../../prototype/components/icons';
import ui from '../../prototype/components/ui.module.css';
import styles from '../../forum/forum.module.css';

export default function StudentDashboard() {
  const [stats, setStats] = useState({ chats: 0, documents: 0, flashcards: 0, discussions: 0 });
  const [error, setError] = useState('');
  const profile = getProfile();
  useEffect(() => {
    Promise.allSettled([
      apiFetch('/students/chats/'),
      apiFetch('/students/documents/'),
      apiFetch('/students/flashcards/'),
      apiFetch('/forum/posts/'),
    ]).then(results => setStats({
      chats: results[0].status === 'fulfilled' ? (results[0].value.chats || []).length : 0,
      documents: results[1].status === 'fulfilled' ? (results[1].value.documents || []).length : 0,
      flashcards: results[2].status === 'fulfilled' ? (results[2].value.decks || []).reduce((n,d)=>n+(d.cards?.length||0),0) : 0,
      discussions: results[3].status === 'fulfilled' ? (results[3].value.posts || []).length : 0,
    }));
  }, []);

  return <LafreShell role="student" active="Home"><div className={ui.shell}>
    <div className={ui.row}><div><div className={styles.eyebrow}>Student workspace</div><h1 className={ui.title}>{profile?.full_name ? `${profile.full_name.split(' ')[0]}'s LAFRE network.` : 'Your LAFRE network.'}</h1><p className={ui.subtitle}>Use the community forum alongside your existing LAFRE AI study workspace.</p></div><span className={styles.tag}><Icon name="user" size={13}/> Law student</span></div>
    {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={16}/><p>{error}</p></div>}
    <div className={ui.threeCol} style={{marginTop:20}}>
      <Link href="/forum" className={`${ui.panel} ${ui.pad}`} style={{textDecoration:'none',color:'#171717'}}><div className={styles.eyebrow}><Icon name="forum" size={14}/> Community</div><h3>Explore discussions</h3><p className={ui.muted}>Ask study questions, read civilian discussions, and contribute where the forum permissions allow it.</p></Link>
      <Link href="/mentorship" className={`${ui.panel} ${ui.pad}`} style={{textDecoration:'none',color:'#171717'}}><div className={styles.eyebrow}><Icon name="users" size={14}/> Mentorship</div><h3>Find a verified mentor</h3><p className={ui.muted}>Join private professional-development programmes with practising lawyers.</p></Link>
      <Link href="/chat" className={`${ui.panel} ${ui.pad}`} style={{textDecoration:'none',color:'#171717'}}><div className={styles.eyebrow}><Icon name="sparkle" size={14}/> Student AI</div><h3>Open LAFRE AI</h3><p className={ui.muted}>Continue in the existing chatbot, library, documents, and study tools.</p></Link>
    </div>
    <section className={`${ui.panel} ${ui.pad}`} style={{marginTop:22}}><div className={styles.eyebrow}>Live study snapshot</div><div className={ui.threeCol} style={{marginTop:10}}>{[['AI chats',stats.chats,'message'],['Library documents',stats.documents,'brief'],['Saved flashcards',stats.flashcards,'tool'],['Visible discussions',stats.discussions,'forum']].map(([label,value,icon])=><div className={ui.listItem} key={label}><div className={ui.row}><span className={styles.avatar}><Icon name={icon} size={14}/></span><span style={{fontSize:12}}>{label}</span><strong>{value}</strong></div></div>)}</div></section>
    <section className={`${ui.panel} ${ui.pad}`} style={{marginTop:16}}><div className={styles.eyebrow}>Private lawyer questions</div><h2 style={{fontSize:20,margin:'5px 0'}}>Ask through the forum</h2><p className={ui.muted} style={{fontSize:13,lineHeight:1.6}}>A discussion created by a student is handled as a student-only question by the backend, so verified lawyers can respond while the question remains protected from other students and public visitors.</p><Link className={styles.primaryButton} href="/forum"><Icon name="forum" size={15}/> Start a student question</Link></section>
  </div></LafreShell>;
}
