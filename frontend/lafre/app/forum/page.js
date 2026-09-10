'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../lib/api';
import ui from '../prototype/components/ui.module.css';

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
  return <LafreShell active="Forum"><div className={ui.shell}><div className={ui.eyebrow}>LAFRE forum</div><h1 className={ui.title}>Legal questions, real conversations.</h1><p className={ui.subtitle}>Discussions are loaded from the LAFRE backend and visibility follows your account role.</p>{error && <div className={ui.panel + ' ' + ui.pad}><p>{error}</p></div>}{notice && <div className={ui.panel + ' ' + ui.pad}><p>{notice}</p></div>}{profile && <form onSubmit={submit} className={ui.panel + ' ' + ui.pad} style={{ margin: '20px 0' }}><h2 style={{ fontSize: 19, marginTop: 0 }}>Start a discussion</h2><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Title" style={{ width: '100%', padding: 10, marginBottom: 8 }} /><select value={community} onChange={(event) => setCommunity(event.target.value)} style={{ width: '100%', padding: 10, marginBottom: 8 }}><option value="">Choose a community</option>{communities.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Describe your question" rows={4} style={{ width: '100%', padding: 10 }} /><button className={ui.goldBtn} type="submit" style={{ marginTop: 10 }}>Post discussion</button></form>}{posts.map((post) => <article className={ui.panel + ' ' + ui.pad} key={post.id} style={{ marginBottom: 12 }}><div className={ui.eyebrow}>{post.community_detail?.name || post.author_role}</div><h2 style={{ fontSize: 19 }}><Link href={`/forum/${post.id}`}>{post.title}</Link></h2><p>{post.text}</p><span className={ui.muted}>{post.reply_count || 0} replies · {post.like_count || 0} likes</span></article>)}{!posts.length && !error && <p className={ui.muted}>No discussions are available yet.</p>}</div></LafreShell>;
}
