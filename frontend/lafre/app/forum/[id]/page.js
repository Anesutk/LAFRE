'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import LafreShell from '../../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../../lib/api';
import { Icon } from '../../prototype/components/icons';
import ui from '../../prototype/components/ui.module.css';
import styles from '../forum.module.css';

function formatDate(value) {
  if (!value) return 'Just now';
  try { return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)); }
  catch { return 'Recent'; }
}

function roleFor(profile) {
  if (profile?.role === 'student' || profile?.can_use_student) return 'student';
  if (profile?.role === 'lawyer' || profile?.can_access_lawyer_portal) return 'lawyer';
  if (profile?.role === 'citizen' || profile?.can_use_civilian) return 'civilian';
  return 'visitor';
}

function RoleBadge({ role }) {
  const label = role === 'lawyer' ? 'Verified lawyer' : role === 'student' ? 'Law student' : 'Community member';
  return <span className={styles.roleBadge}>{role === 'lawyer' ? '★★★ ' : role === 'student' ? '★ ' : ''}{label}</span>;
}

export default function QuestionPage() {
  const { id } = useParams();
  const profile = getProfile();
  const role = roleFor(profile);
  const [post, setPost] = useState(null);
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [action, setAction] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    if (!id) return;
    setLoading(true); setError('');
    try { const result = await apiFetch(`/forum/posts/${id}/`); setPost(result.post); }
    catch (err) { setError(err.message || 'Could not load this discussion.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, [id]);

  const canReply = useMemo(() => {
    if (!profile || profile.status !== 'approved') return false;
    if (!post) return false;
    if (post.author_role === 'student') return role === 'lawyer';
    return role === 'student' || role === 'lawyer';
  }, [profile, post, role]);

  async function toggle(kind) {
    if (!post) return;
    setAction(kind); setError('');
    try {
      const result = await apiFetch(`/forum/posts/${post.id}/${kind}/`, { method: 'POST', body: JSON.stringify({}) });
      setPost(current => current ? { ...current, ...(kind === 'like' ? { liked: !!result.liked, like_count: result.like_count } : { saved: !!result.saved }) } : current);
    } catch (err) { setError(err.message || `Could not ${kind} this discussion.`); }
    finally { setAction(''); }
  }

  async function submitReply(e) {
    e.preventDefault(); setError(''); setNotice('');
    if (!canReply) { setError(post?.author_role === 'student' ? 'Only verified lawyers can respond to a student-only question.' : 'Sign in with an approved student or lawyer account to reply.'); return; }
    if (!reply.trim()) { setError('Write a reply before posting.'); return; }
    setSubmitting(true);
    try {
      await apiFetch(`/forum/posts/${post.id}/comments/`, { method: 'POST', body: JSON.stringify({ text: reply.trim() }) });
      setReply(''); setNotice('Reply posted.'); await load();
    } catch (err) { setError(err.message || 'Could not post your reply.'); }
    finally { setSubmitting(false); }
  }

  async function sharePost() {
    const url = window.location.href;
    try {
      if (navigator.share) await navigator.share({ title: post?.title || 'LAFRE discussion', url });
      else { await navigator.clipboard.writeText(url); setNotice('Discussion link copied.'); }
    } catch { /* user cancelled the share sheet */ }
  }

  return <LafreShell role={role} active="Forum">
    <div className={`${ui.shell} ${styles.forumPage}`}>
      <div className={styles.detailTop}><Link href="/forum" className={styles.backLink}><Icon name="arrow" size={14} /> Forum</Link></div>
      {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={17} /><p>{error}</p></div>}
      {notice && <div className={`${ui.panel} ${ui.pad} ${styles.notice}`}><Icon name="like" size={17} /><p>{notice}</p></div>}

      {loading ? <div className={`${ui.panel} ${ui.pad} ${styles.loading}`}><span className={styles.spinner} /> Loading discussion…</div> : post ? <div className={styles.detailGrid}>
        <main>
          <article className={`${ui.panel} ${ui.pad} ${styles.detailCard}`}>
            <div className={styles.detailMeta}><span className={styles.tag}><Icon name="forum" size={12} /> {post.community_detail?.name || 'General'}</span><span>{formatDate(post.created_at)}</span></div>
            <h1>{post.title}</h1>
            <div className={styles.authorRow}><span className={styles.avatarLarge}><Icon name="user" size={17} /></span><div><strong>{post.author_name || 'LAFRE member'}</strong><RoleBadge role={post.author_role} /></div></div>
            <p className={styles.detailText}>{post.text}</p>
            <div className={styles.actionBar}>
              <button className={`${styles.detailAction} ${post.liked ? styles.actionActive : ''}`} disabled={!!action} onClick={() => toggle('like')}><Icon name="like" size={16} /> {post.like_count || 0} Like</button>
              <button className={`${styles.detailAction} ${post.saved ? styles.actionActive : ''}`} disabled={!!action} onClick={() => toggle('save')}><Icon name="bookmark" size={16} /> {post.saved ? 'Saved' : 'Save'}</button>
              <button className={styles.detailAction} onClick={sharePost}><Icon name="share" size={16} /> Share</button>
            </div>
          </article>

          <section className={`${ui.panel} ${ui.pad}`} style={{ marginTop: 16 }}>
            <div className={styles.responseHeader}><div><div className={styles.eyebrow}>Community replies</div><h2>Responses</h2></div><span>{post.comments?.length || 0}</span></div>
            {post.comments?.length ? <div className={styles.responses}>{post.comments.map(comment => <article className={styles.response} key={comment.id}><div className={styles.authorRow}><span className={styles.avatarLarge}><Icon name={comment.is_ai_generated ? 'sparkle' : 'user'} size={16} /></span><div><strong>{comment.author_name || 'LAFRE'}</strong> <RoleBadge role={comment.author_role} /><div className={styles.responseTime}>{formatDate(comment.created_at)}</div></div></div><p>{comment.text}</p></article>)}</div> : <div className={styles.emptyResponses}><Icon name="message" size={26} /><p>No replies yet.</p><span>Be the first person to contribute where the forum permissions allow it.</span></div>}
          </section>

          <section className={`${ui.panel} ${ui.pad}`} style={{ marginTop: 16 }}>
            <div className={styles.eyebrow}>Join the discussion</div>
            {post.author_role === 'student' && role !== 'lawyer' ? <div className={styles.permissionNote}><Icon name="lawyer" size={17} /><span>This student question is restricted to the author and verified lawyers. A verified lawyer can respond here.</span></div> : null}
            {!profile ? <div className={styles.permissionNote}><Icon name="user" size={17} /><span>Sign in to participate in this discussion.</span><Link href="/login">Sign in</Link></div> : null}
            {profile && profile.status !== 'approved' ? <div className={styles.permissionNote}><Icon name="flag" size={17} /><span>Your account is waiting for approval before you can post replies.</span></div> : null}
            {canReply && <form onSubmit={submitReply}><textarea className={styles.replyBox} value={reply} onChange={e => setReply(e.target.value)} placeholder="Write a clear, respectful response…" rows={5} maxLength={5000} /><div className={styles.replyFooter}><span>{reply.length}/5000</span><button className={styles.primaryButton} disabled={submitting}><Icon name="arrow" size={15} /> {submitting ? 'Posting…' : 'Post response'}</button></div></form>}
          </section>
        </main>
        <aside>
          <div className={`${ui.panel} ${ui.pad} ${styles.sideCard}`}><div className={styles.eyebrow}>Need professional help?</div><h3>Move from public discussion to a lawyer.</h3><p>Browse verified lawyers for professional services rather than sharing confidential information publicly.</p><Link href="/lawyers" className={styles.secondaryButton}><Icon name="lawyer" size={15} /> Find lawyers</Link></div>
        </aside>
      </div> : null}
    </div>
  </LafreShell>;
}
