'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../lib/api';
import ui from '../prototype/components/ui.module.css';
import styles from './forum.module.css';

export default function ForumPage() {
  const [posts, setPosts] = useState([]);
  const [communities, setCommunities] = useState([]);
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [community, setCommunity] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  async function load() { try { const [postResult, communityResult] = await Promise.all([apiFetch('/forum/posts/'), apiFetch('/forum/communities/')]); setPosts(postResult.posts || []); setCommunities(communityResult.communities || []); } catch (err) { setError(err.message || 'Could not load the forum.'); } }
  useEffect(() => { load(); }, []);
  async function submit(event) { event.preventDefault(); setError(''); setNotice(''); if (!title.trim() || !text.trim() || !community) { setError('Title, community, and question are required.'); return; } try { await apiFetch('/forum/posts/', { method: 'POST', body: JSON.stringify({ title: title.trim(), text: text.trim(), community: Number(community) }) }); setTitle(''); setText(''); setNotice('Your discussion was posted.'); await load(); } catch (err) { setError(err.message || 'Could not post the discussion.'); } }
  const profile = getProfile();
  const role = profile?.role === 'student' || profile?.can_use_student ? 'student' : profile?.role === 'lawyer' ? 'lawyer' : 'visitor';
  return <LafreShell role={role} active="Forum"><div className={`${ui.shell} ${styles.forumPage}`}>
    <header className={styles.hero}>
      <div className={styles.heroIcon}>✦</div>
      <div><div className={styles.eyebrow}>Student legal community</div><h1 className={ui.title}>Ask clearly. Learn together.</h1><p className={ui.subtitle}>A focused forum for law students to exchange questions, find perspective from practising lawyers, and move into LAFRE AI when they need deeper study help.</p></div>
      {role === 'student' && <Link href="/chat" className={styles.chatLink}><span>✦</span> Open AI chat</Link>}
    </header>
    {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><span>!</span><p>{error}</p></div>}
    {notice && <div className={`${ui.panel} ${ui.pad} ${styles.notice}`}><span>✓</span><p>{notice}</p></div>}
    {profile && <form onSubmit={submit} className={`${ui.panel} ${ui.pad} ${styles.composer}`}>
      <div className={styles.sectionHeading}><span className={styles.headingIcon}>✎</span><div><h2>Start a discussion</h2><p>Share a question your fellow students or a verified lawyer can help unpack.</p></div></div>
      <div className={styles.fields}><label><span>Discussion title</span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="What would you like to understand?" /></label><label><span>Community</span><select value={community} onChange={(event) => setCommunity(event.target.value)}><option value="">Choose a community</option>{communities.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div>
      <label className={styles.messageField}><span>Your question</span><textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Describe the facts, rule, or case you are working through…" rows={4} /></label>
      <div className={styles.composerFooter}><span className={styles.helper}><span>◎</span> Keep personal and confidential details out of public posts.</span><button className={styles.primaryButton} type="submit"><span>➤</span> Post discussion</button></div>
    </form>}
    <div className={styles.feedHeader}><div><div className={styles.eyebrow}>Community feed</div><h2>Recent discussions</h2></div><span className={styles.feedCount}>{posts.length} conversations</span></div>
    <div className={styles.feed}>{posts.map((post) => <article className={`${ui.panel} ${styles.post}`} key={post.id}><div className={styles.postAccent} /><div className={styles.postBody}><div className={styles.postMeta}><span className={styles.avatar}>♙</span><span>{post.author_name || 'LAFRE member'} · {post.author_role || 'community member'}</span><span className={styles.dot}>•</span><span>{post.community_detail?.name || 'General'}</span></div><h2><Link href={`/forum/${post.id}`}>{post.title}</Link></h2><p>{post.text}</p><div className={styles.postFooter}><span>◌ {post.reply_count || 0} replies</span><span>♡ {post.like_count || 0} likes</span><Link href={`/forum/${post.id}`}>Read discussion <span>→</span></Link></div></div></article>)}</div>
    {!posts.length && !error && <div className={`${ui.panel} ${styles.empty}`}><span>✦</span><h3>No discussions yet</h3><p>Start the first student conversation above.</p></div>}
  </div></LafreShell>;
}
