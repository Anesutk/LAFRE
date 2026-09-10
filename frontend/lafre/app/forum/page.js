'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import LafreShell from '../prototype/components/LafreShell';
import { apiFetch, getProfile } from '../lib/api';
import { Icon } from '../prototype/components/icons';
import ui from '../prototype/components/ui.module.css';
import styles from './forum.module.css';

function formatDate(value) {
  if (!value) return 'Just now';
  try {
    return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
  } catch {
    return 'Recent';
  }
}

function profileRole(profile) {
  if (profile?.role === 'student' || profile?.can_use_student) return 'student';
  if (profile?.role === 'lawyer' || profile?.can_access_lawyer_portal) return 'lawyer';
  if (profile?.role === 'citizen' || profile?.can_use_civilian) return 'civilian';
  return 'visitor';
}

function ForumPageInner() {
  const searchParams = useSearchParams();
  const category = searchParams.get('category') || '';
  const profile = getProfile();
  const role = profileRole(profile);
  const [posts, setPosts] = useState([]);
  const [communities, setCommunities] = useState([]);
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [community, setCommunity] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [actionId, setActionId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const query = category ? `?category=${encodeURIComponent(category)}` : '';
      const [postResult, communityResult] = await Promise.all([
        apiFetch(`/forum/posts/${query}`),
        apiFetch('/forum/communities/'),
      ]);
      setPosts(postResult.posts || []);
      setCommunities(communityResult.communities || []);
      if (!community && !category && communityResult.communities?.length) {
        setCommunity(String(communityResult.communities[0].id));
      }
    } catch (err) {
      setError(err.message || 'Could not load the forum.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category]);

  const activeCategory = useMemo(() => category || 'All discussions', [category]);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    if (role === 'visitor') {
      setError('Sign in as a student to start a discussion.');
      return;
    }
    if (profile?.status !== 'approved') {
      setError('Your account must be approved before you can post.');
      return;
    }
    if (!title.trim() || !text.trim() || !community) {
      setError('Title, community, and question are required.');
      return;
    }
    setPosting(true);
    try {
      await apiFetch('/forum/posts/', {
        method: 'POST',
        body: JSON.stringify({
          title: title.trim(),
          text: text.trim(),
          community: Number(community),
          language: 'en',
        }),
      });
      setTitle('');
      setText('');
      setNotice('Your discussion was posted successfully.');
      await load();
    } catch (err) {
      setError(err.message || 'Could not post the discussion.');
    } finally {
      setPosting(false);
    }
  }

  async function togglePost(postId, kind) {
    setActionId(`${kind}-${postId}`);
    setError('');
    try {
      const result = await apiFetch(`/forum/posts/${postId}/${kind}/`, {
        method: 'POST',
        body: JSON.stringify({}),
      });
      setPosts((current) => current.map((post) => post.id === postId ? {
        ...post,
        ...(kind === 'like'
          ? { liked: !!result.liked, like_count: result.like_count }
          : { saved: !!result.saved }),
      } : post));
    } catch (err) {
      setError(err.message || `Could not ${kind} this post.`);
    } finally {
      setActionId(null);
    }
  }

  return (
    <LafreShell role={role} active="Forum">
      <div className={`${ui.shell} ${styles.forumPage}`}>
        <header className={styles.hero}>
          <div className={styles.heroIcon}><Icon name="forum" size={25} /></div>
          <div className={styles.heroCopy}>
            <div className={styles.eyebrow}>LAFRE Forum</div>
            <h1 className={ui.title}>Ask clearly. Learn together.</h1>
            <p className={ui.subtitle}>Discuss real legal questions, learn from other community members, and hear from verified lawyers where appropriate.</p>
          </div>
          {role === 'student' && <Link href="/chat" className={styles.chatLink}><Icon name="sparkle" size={16} /> Open AI chat</Link>}
        </header>
        {error && <div className={`${ui.panel} ${ui.pad} ${styles.alert}`}><Icon name="flag" size={17} /><p>{error}</p></div>}
        {notice && <div className={`${ui.panel} ${ui.pad} ${styles.notice}`}><Icon name="like" size={17} /><p>{notice}</p></div>}
        {role !== 'visitor' && <form onSubmit={submit} className={`${ui.panel} ${ui.pad} ${styles.composer}`}>
          <div className={styles.sectionHeading}><span className={styles.headingIcon}><Icon name="plus" size={17} /></span><div><h2>Start a discussion</h2><p>Keep public questions clear and avoid unnecessary confidential details.</p></div></div>
          <div className={styles.fields}>
            <label><span>Discussion title</span><input value={title} onChange={e => setTitle(e.target.value)} placeholder="What would you like to understand?" maxLength={220} /></label>
            <label><span>Community</span><select value={community} onChange={e => setCommunity(e.target.value)}><option value="">Choose a community</option>{communities.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          </div>
          <label className={styles.messageField}><span>Your question</span><textarea value={text} onChange={e => setText(e.target.value)} placeholder="Describe the facts, rule, case, or study question…" rows={5} /></label>
          <div className={styles.composerFooter}><span className={styles.helper}><Icon name="flag" size={13} /> Student posts are visible according to LAFRE forum permissions.</span><button className={styles.primaryButton} type="submit" disabled={posting}><Icon name="arrow" size={15} /> {posting ? 'Posting…' : 'Post discussion'}</button></div>
        </form>}
        <div className={styles.feedHeader}><div><div className={styles.eyebrow}>Community feed</div><h2>{activeCategory}</h2></div><span className={styles.feedCount}>{loading ? 'Loading…' : `${posts.length} conversation${posts.length === 1 ? '' : 's'}`}</span></div>
        {loading ? <div className={`${ui.panel} ${ui.pad} ${styles.loading}`}><span className={styles.spinner} /> Loading discussions…</div> : <div className={styles.feed}>
          {posts.map(post => <article className={`${ui.panel} ${styles.post}`} key={post.id}>
            <div className={styles.postAccent} />
            <div className={styles.postBody}>
              <div className={styles.postMeta}><span className={styles.avatar}><Icon name="user" size={14} /></span><span>{post.author_name || 'LAFRE member'}</span><span>·</span><span>{post.author_role || 'community member'}</span><span>·</span><span>{post.community_detail?.name || 'General'}</span><span>·</span><span>{formatDate(post.created_at)}</span></div>
              <h2><Link href={`/forum/${post.id}`}>{post.title}</Link></h2>
              <p>{post.text}</p>
              <div className={styles.postFooter}>
                <button className={`${styles.inlineAction} ${post.liked ? styles.actionActive : ''}`} disabled={actionId === `like-${post.id}`} onClick={() => togglePost(post.id, 'like')}><Icon name="like" size={14} /> {post.like_count || 0}</button>
                <span><Icon name="message" size={14} /> {post.reply_count || 0} replies</span>
                <button className={`${styles.inlineAction} ${post.saved ? styles.actionActive : ''}`} disabled={actionId === `save-${post.id}`} onClick={() => togglePost(post.id, 'save')}><Icon name="bookmark" size={14} /> {post.saved ? 'Saved' : 'Save'}</button>
                <Link href={`/forum/${post.id}`}>Read discussion <Icon name="arrow" size={14} /></Link>
              </div>
            </div>
          </article>)}
        </div>}
        {!loading && !posts.length && !error && <div className={`${ui.panel} ${styles.empty}`}><Icon name="forum" size={30} /><h3>No discussions here yet</h3><p>{role === 'visitor' ? 'Sign in to start a conversation.' : 'Start the first discussion in this community.'}</p></div>}
      </div>
    </LafreShell>
  );
}

export default function ForumPage() {
  return (
    <Suspense fallback={<div style={{ padding: 40 }}>Loading forum…</div>}>
      <ForumPageInner />
    </Suspense>
  );
}
