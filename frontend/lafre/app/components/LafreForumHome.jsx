'use client';

import { useMemo, useState } from 'react';
import styles from './LafreForumHome.module.css';

// Communities replace the old clinical "Employment Law / Criminal Law" category labels -
// same underlying grouping, but named and coloured like an actual community rather than a
// legal taxonomy admin panel.
const communities = [
  { key: 'workplace', name: 'Workplace & Employment', color: '#f97316' },
  { key: 'family', name: 'Family Matters', color: '#3b82f6' },
  { key: 'criminal', name: 'Criminal Justice', color: '#ef4444' },
  { key: 'housing', name: 'Housing & Property', color: '#10b981' },
  { key: 'contracts', name: 'Contracts & Agreements', color: '#8b5cf6' },
  { key: 'business', name: 'Business & Startups', color: '#14b8a6' },
  { key: 'rights', name: 'Rights & Constitution', color: '#d99a2b' },
];
const communityByKey = Object.fromEntries(communities.map((c) => [c.key, c]));

const initialPosts = [
  { id: 1, user: 'Tendai M.', role: 'public', community: 'workplace', time: '2h ago', title: 'Can my employer terminate me without notice?', text: 'I have been working with my company for 3 years. Yesterday I was told my services are no longer needed effective immediately. Is this legal?', replies: 18, views: 286, likes: 42 },
  { id: 2, user: 'Sarah N.', role: 'public', community: 'housing', time: '4h ago', title: 'What rights do I have as a tenant?', text: 'My landlord wants me to leave the property within 7 days without giving me a reason. What are my rights as a tenant?', replies: 11, views: 194, likes: 27 },
  { id: 3, user: 'John M.', role: 'public', community: 'criminal', time: '5h ago', title: 'Can a police officer search my phone without a warrant?', text: 'I was stopped and asked to unlock my phone. I would like to understand the general legal position.', replies: 24, views: 352, likes: 39 },
  { id: 4, user: 'Rudo K.', role: 'student', community: 'rights', time: '6h ago', title: 'Question for practising lawyers: interpreting constitutional rights', text: 'I am a law student looking for guidance on how practising lawyers approach conflicting constitutional rights in real cases.', replies: 9, views: 128, likes: 21, studentOnly: true },
];
const trending = [
  { title: 'Can my employer terminate me without notice?', likes: 42 },
  { title: 'Can a police officer search my phone without a warrant?', likes: 39 },
  { title: 'What rights do I have as a tenant?', likes: 27 },
];
const recent = [
  { title: 'Question for practising lawyers: constitutional rights', time: '6h ago' },
  { title: 'What rights do I have as a tenant?', time: '4h ago' },
  { title: 'Can my employer terminate me without notice?', time: '2h ago' },
];
const tools = [
  { name: 'Document Checker', icon: '▤', color: '#3b82f6', desc: 'Check a legal document for important terms and possible issues.' },
  { name: 'Clause Checker', icon: '⌑', color: '#8b5cf6', desc: 'Find important clauses and explain what they generally mean.' },
  { name: 'Document Explainer', icon: '◫', color: '#10b981', desc: 'Turn complex legal language into easier information.' },
  { name: 'Affidavit Drafting', icon: '✎', color: '#f97316', desc: 'Create a structured starting draft with AI assistance.' },
];
const mockLawyers = [
  { name: 'Adv. Tapiwa Moyo', area: 'Employment Law', rating: '4.9', reviews: 128 },
  { name: 'Adv. Brian Chikore', area: 'Commercial Law', rating: '4.8', reviews: 96 },
  { name: 'Adv. Rudo Ncube', area: 'Family Law', rating: '4.9', reviews: 74 },
];

function initials(name) { return name.split(' ').map((p) => p[0]).slice(0, 2).join(''); }
function avatarColor(name) { const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f97316', '#ec4899', '#14b8a6']; let sum = 0; for (const c of name) sum += c.charCodeAt(0); return colors[sum % colors.length]; }

export default function LafreForumHome() {
  const [community, setCommunity] = useState('all');
  const [search, setSearch] = useState('');
  const [menu, setMenu] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(true); // expanded by default, per spec
  const [communitiesOpen, setCommunitiesOpen] = useState(true);
  const [liked, setLiked] = useState([]);
  const [saved, setSaved] = useState([]);
  const [posts, setPosts] = useState(initialPosts);
  const [draft, setDraft] = useState('');
  // Simulated post flow: idle -> posting -> analyzing -> suggesting -> done. This is a
  // stand-in for the real AI + lawyer-recommendation pipeline, built after auth is in place -
  // for the prototype it's just a timed state machine with no real backend call.
  const [flowStep, setFlowStep] = useState('idle');
  const [suggestedLawyer, setSuggestedLawyer] = useState(null);
  const [newPostId, setNewPostId] = useState(null);

  const visible = useMemo(() => posts.filter((p) => {
    const inCommunity = community === 'all' || p.community === community;
    const q = search.trim().toLowerCase();
    return inCommunity && (!q || `${p.title} ${p.text}`.toLowerCase().includes(q));
  }), [posts, community, search]);

  const toggle = (setter, id) => setter((v) => (v.includes(id) ? v.filter((x) => x !== id) : [...v, id]));

  function submitPost() {
    if (!draft.trim() || flowStep !== 'idle') return;
    setFlowStep('posting');
    setTimeout(() => setFlowStep('analyzing'), 700);
    setTimeout(() => setFlowStep('suggesting'), 1600);
    setTimeout(() => {
      setSuggestedLawyer(mockLawyers[Math.floor(Math.random() * mockLawyers.length)]);
      setFlowStep('suggested');
    }, 2500);
  }
  function confirmPost() {
    const id = Date.now();
    setPosts((p) => [{ id, user: 'You', role: 'public', community: 'workplace', time: 'just now', title: draft.slice(0, 90), text: draft, replies: 0, views: 1, likes: 0 }, ...p]);
    setNewPostId(id);
    setDraft(''); setFlowStep('idle'); setSuggestedLawyer(null);
    setTimeout(() => setNewPostId(null), 1500);
  }

  return <div className={styles.app}>
    <header className={styles.topbar}>
      <div className={styles.topInner}>
        <a href="/" className={styles.brand}><span className={styles.mark}>⚖</span><span><b>LAFRE</b><small>LAW · COMMUNITY · SOLUTIONS</small></span></a>
        <button className={styles.menu} onClick={() => setMenu(!menu)}>☰</button>
        <label className={styles.search}><span>⌕</span><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search discussions, lawyers, topics..." /></label>
        <div className={styles.topActions}>
          <a href="/login" className={styles.login}>Log in</a>
          <a href="/register" className={styles.signup}>Sign up</a>
        </div>
      </div>
    </header>

    <div className={styles.layout}>
      <aside className={`${styles.sidebar} ${menu ? styles.sidebarOpen : ''}`}>
        <a className={styles.navLink} href="/" title="Home"><span className={styles.iconSwatch} style={{ background: '#eef2ff', color: '#3b82f6' }}>⌂</span> Home</a>
        <a className={styles.navLink} href="/chat" title="AI Legal Chatbot"><span className={styles.iconSwatch} style={{ background: '#ecfdf5', color: '#10b981' }}>✦</span> AI Chatbot</a>

        <button className={styles.sectionToggle} onClick={() => setToolsOpen((v) => !v)}>Tools <span className={`${styles.arrow} ${toolsOpen ? styles.arrowOpen : ''}`}>›</span></button>
        <div className={`${styles.subLinks} ${toolsOpen ? styles.subLinksOpen : ''}`}>
          {tools.map((t) => <button key={t.name} className={styles.subLink} title={t.desc} onClick={() => alert(t.name + ' is a frontend demo for now.')}>
            <span className={styles.iconSwatch} style={{ width: 20, height: 20, fontSize: 11, background: t.color + '1a', color: t.color }}>{t.icon}</span> {t.name}
          </button>)}
        </div>

        <div className={styles.divider} />
        <div className={styles.accountBox}>
          <p>Log in to post questions, save discussions, and connect with verified lawyers.</p>
          <div className={styles.accountBtns}><a href="/login" style={{ border: '1px solid var(--line)', color: 'var(--ink)' }}>Log in</a><a href="/register" className={styles.goldBtn}>Sign up</a></div>
        </div>
        <div className={styles.divider} />

        <button className={styles.sectionToggle} onClick={() => setCommunitiesOpen((v) => !v)}>Communities <span className={`${styles.arrow} ${communitiesOpen ? styles.arrowOpen : ''}`}>›</span></button>
        <div className={`${styles.subLinks} ${communitiesOpen ? styles.subLinksOpen : ''}`} style={{ maxHeight: communitiesOpen ? 400 : 0 }}>
          <button className={styles.communityRow} onClick={() => { setCommunity('all'); setMenu(false); }}><span className={styles.communityDot} style={{ background: '#a39c8c' }} /> All communities</button>
          {communities.map((c) => <button key={c.key} className={styles.communityRow} onClick={() => { setCommunity(c.key); setMenu(false); }}><span className={styles.communityDot} style={{ background: c.color }} /> {c.name}</button>)}
        </div>

        <div className={styles.sectionToggle} style={{ cursor: 'default' }}>Popular</div>
        {trending.slice(0, 3).map((t) => <a key={t.title} href="#" className={styles.popularItem}><b>{t.title}</b><span>{t.likes} likes</span></a>)}
      </aside>

      <main className={styles.main}>
        <div className={styles.composer}>
          <textarea rows={2} placeholder="Ask a legal question or start a discussion..." value={draft} onChange={(e) => setDraft(e.target.value)} disabled={flowStep !== 'idle'} />
          <div className={styles.composerFoot}>
            {flowStep === 'idle' && <span className={styles.composerHint}>Posting requires an account — you'll be asked to log in.</span>}
            {flowStep === 'posting' && <span className={styles.composerStatus}><span className={styles.dotPulse} /> Posting your question…</span>}
            {flowStep === 'analyzing' && <span className={styles.composerStatus}><span className={styles.dotPulse} /> AI is reviewing your question…</span>}
            {flowStep === 'suggesting' && <span className={styles.composerStatus}><span className={styles.dotPulse} /> Finding a lawyer who can help…</span>}
            {flowStep === 'suggested' && <span className={styles.composerStatus}>Ready to post</span>}
            <button className={styles.goldBtn} onClick={flowStep === 'suggested' ? confirmPost : submitPost} disabled={!draft.trim() || (flowStep !== 'idle' && flowStep !== 'suggested')}>
              {flowStep === 'suggested' ? 'Confirm & Post' : 'Post'}
            </button>
          </div>
          {flowStep === 'suggested' && suggestedLawyer && <div className={styles.lawyerSuggest}>
            <div className={styles.av}>{initials(suggestedLawyer.name)}</div>
            <div><b>{suggestedLawyer.name}</b> <span className={styles.stars}>★★★</span><span className={styles.tagPromo}>Recommended</span>
              <p>{suggestedLawyer.area} · ★ {suggestedLawyer.rating} ({suggestedLawyer.reviews} reviews) — may be a good fit for this question.</p>
            </div>
          </div>}
        </div>

        <div className={styles.pills}>
          <button className={community === 'all' ? styles.pillActive : ''} onClick={() => setCommunity('all')}>All</button>
          {communities.map((c) => <button key={c.key} className={community === c.key ? styles.pillActive : ''} onClick={() => setCommunity(c.key)}>{c.name}</button>)}
        </div>

        <div className={styles.feed}>
          {visible.map((p) => {
            const c = communityByKey[p.community];
            return <article key={p.id} className={p.id === newPostId ? styles.post + ' ' + styles.postNew : styles.post}>
              <div className={styles.vote}>
                <button onClick={() => toggle(setLiked, p.id)} className={liked.includes(p.id) ? styles.voted : ''}>↑</button>
                <b>{p.likes + (liked.includes(p.id) ? 1 : 0)}</b>
                <button>↓</button>
              </div>
              <div className={styles.postBody}>
                <div className={styles.meta}>
                  <span className={styles.avatar} style={{ background: avatarColor(p.user) }}>{initials(p.user)}</span>
                  <span><b>{p.user}</b> · {p.role === 'student' ? <strong className={styles.student}>★ Law Student</strong> : 'Public user'} · {p.time}</span>
                </div>
                <a href="#" className={styles.postTitle}>{p.title}</a>
                <div>{c && <span className={styles.communityTag} style={{ background: c.color + '1a', color: c.color }}><span className={styles.communityDot} style={{ background: c.color }} /> {c.name}</span>}{p.studentOnly && <span className={styles.lawyerOnly}>Lawyer responses only</span>}</div>
                <p className={styles.excerpt}>{p.text}</p>
                <div className={styles.actions}>
                  <button>◌ {p.replies} Replies</button>
                  <button>◉ {p.views}</button>
                  <button onClick={() => toggle(setSaved, p.id)} className={saved.includes(p.id) ? styles.saved : ''}>♡ {saved.includes(p.id) ? 'Saved' : 'Save'}</button>
                  <button>↗ Share</button>
                </div>
              </div>
            </article>;
          })}
          {!visible.length && <div className={styles.empty}>No discussions match your current search or community.</div>}
        </div>
      </main>

      <aside className={styles.right}>
        <div className={styles.card}>
          <div className={styles.cardHead}><span className={styles.fire}>🔥</span> Trending</div>
          {trending.map((t) => <div key={t.title} className={styles.trendItem}><b>{t.title}</b><span>{t.likes}</span></div>)}
        </div>
        <div className={styles.card}>
          <div className={styles.cardHead}>🕐 Recent posts</div>
          {recent.map((r) => <div key={r.title} className={styles.trendItem}><b>{r.title}</b><span>{r.time}</span></div>)}
        </div>
      </aside>
    </div>
    <footer className={styles.footer}><span>© 2026 LAFRE</span><span>Legal community · Professional networking · AI-assisted tools</span><span>General information only · Not legal advice</span></footer>
  </div>;
}
