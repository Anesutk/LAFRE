'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import LafreShell from '../../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../../lib/api';
import { Icon } from '../../prototype/components/icons';
import ui from '../../prototype/components/ui.module.css';
import styles from '../../forum/forum.module.css';

function formatDate(value) { try { return new Intl.DateTimeFormat('en', {dateStyle:'medium', timeStyle:'short'}).format(new Date(value)); } catch { return 'Recent'; } }

export default function MentorshipDetail() {
  const { id } = useParams();
  const profile = getProfile();
  const [programme, setProgramme] = useState(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [messageText, setMessageText] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    if (!id) return;
    setLoading(true); setError('');
    try { const r = await apiFetch(`/forum/mentorship/${id}/`); setProgramme(r.programme); }
    catch (e) { setError(e.message || 'Could not load this programme.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, [id]);

  async function join() {
    setJoining(true); setError('');
    try { const r = await apiFetch(`/forum/mentorship/${id}/join/`, {method:'POST', body:JSON.stringify({})}); setProgramme(r.programme); setNotice('You joined the mentorship programme.'); }
    catch (e) { setError(e.message || 'Could not join the programme.'); }
    finally { setJoining(false); }
  }

  async function sendMessage(e) {
    e.preventDefault(); setError(''); setNotice('');
    if (!messageText.trim()) return;
    setSending(true);
    try { await apiFetch(`/forum/mentorship/${id}/messages/`, {method:'POST', body:JSON.stringify({text:messageText.trim()})}); setMessageText(''); setNotice('Message sent to the private group.'); await load(); }
    catch (e) { setError(e.message || 'Could not send the message.'); }
    finally { setSending(false); }
  }

  return <LafreShell active="Mentorship" role={profile?.role === 'student' ? 'student' : 'lawyer'}>
    <div className={ui.shell}>
      <div style={{marginBottom:14}}><Link href="/mentorship" className={styles.backLink}><Icon name="arrow" size={14}/> Mentorship</Link></div>
      {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={16}/><p>{error}</p></div>}
      {notice && <div className={`${ui.panel} ${ui.pad} ${styles.notice}`}><Icon name="like" size={16}/><p>{notice}</p></div>}
      {loading ? <div className={`${ui.panel} ${ui.pad} ${styles.loading}`}><span className={styles.spinner}/> Loading programme…</div> : programme ? <>
        <section className={`${ui.panel} ${ui.pad}`}>
          <div className={styles.detailMeta}><span className={styles.tag}><Icon name="users" size={12}/> {programme.area || 'Mentorship'}</span><span>{programme.weeks} weeks</span><span>·</span><span>Mentor: {programme.lawyer_name}</span></div>
          <h1 className={styles.detailCard + ' ' + ui.title} style={{marginTop:12}}>{programme.title}</h1>
          <p className={ui.subtitle}>{programme.description}</p>
          <div className={styles.actionBar} style={{borderTop:0,paddingTop:6}}><span className={styles.tag}>{programme.is_free ? 'Free programme' : `Fee ${programme.fee_amount || ''}`}</span><span style={{fontSize:12,color:'#6d6a64'}}>{programme.student_count || 0} students</span><button className={styles.primaryButton} disabled={joining || programme.joined} onClick={join}><Icon name="users" size={15}/> {programme.joined ? 'Joined' : joining ? 'Joining…' : 'Join private programme'}</button></div>
        </section>
        <div className={ui.twoCol} style={{marginTop:16}}>
          <section className={`${ui.panel} ${ui.pad}`}><div className={styles.eyebrow}>What you will cover</div><div style={{marginTop:10}}>{(programme.topics || []).map((topic,i)=><div className={ui.listItem} key={`${topic}-${i}`}><div className={ui.row}><Icon name="like" size={14}/><span style={{fontSize:13}}>{topic}</span></div></div>)}</div>
            {programme.materials?.length ? <><div className={styles.eyebrow} style={{marginTop:18}}>Materials</div>{programme.materials.map(m=><a key={m.id} className={styles.secondaryButton} style={{marginTop:8,display:'flex'}} href={m.file_url || '#'} target={m.file_url ? '_blank' : undefined} rel="noreferrer"><Icon name="brief" size={15}/>{m.title} · {m.material_type}</a>)}</> : null}
          </section>
          <aside className={`${ui.panel} ${ui.pad}`}><div className={styles.eyebrow}>Private group</div>
            {!programme.joined && profile?.role === 'student' ? <div className={styles.permissionNote}><Icon name="users" size={17}/><span>Join the programme to access group messages.</span></div> : null}
            {(programme.joined || programme.is_mentor) && <><div className={styles.responses}>{programme.messages?.length ? programme.messages.map(m=><article className={styles.response} key={m.id}><div className={styles.authorRow}><span className={styles.avatarLarge}><Icon name="user" size={15}/></span><div><strong>{m.author_name}</strong><div className={styles.responseTime}>{formatDate(m.created_at)}</div></div></div><p>{m.text}</p></article>) : <div className={styles.emptyResponses}><Icon name="message" size={25}/><p>No messages yet.</p></div>}</div><form onSubmit={sendMessage}><textarea className={styles.replyBox} value={messageText} onChange={e=>setMessageText(e.target.value)} placeholder="Write to the private group…" rows={4}/><button className={styles.primaryButton} disabled={sending}>{sending ? 'Sending…' : 'Send message'}</button></form></>}
          </aside>
        </div>
      </> : null}
    </div>
  </LafreShell>;
}
