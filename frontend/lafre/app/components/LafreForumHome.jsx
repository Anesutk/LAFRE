'use client';

import { Suspense, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import styles from './LafreForumHome.module.css';
import { lawyers, mentorship, mentorshipMaterials, mentorshipMessages } from '../prototype/mock-api';

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
const mockLawyers = lawyers;
const findLawyerCategories = ['Family Law', 'Criminal Law', 'Employment Law', 'Property Law', 'Business Law', 'Something else'];

function initials(name) { return name.split(' ').map((p) => p[0]).slice(0, 2).join(''); }
function avatarColor(name) { const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f97316', '#ec4899', '#14b8a6']; let sum = 0; for (const c of name) sum += c.charCodeAt(0); return colors[sum % colors.length]; }
// Very rough English-vs-other-language heuristic for the prototype - a real deployment
// would use a proper language-detection library or the model itself, but for a mock demo
// this is enough to demonstrate "AI does not answer in unsupported languages" behaviour.
function looksLikeEnglish(text) {
  const common = ['the', 'is', 'what', 'can', 'my', 'how', 'do', 'i', 'a', 'to', 'and', 'for', 'in', 'of'];
  const words = text.toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return true;
  const hits = words.filter((w) => common.includes(w)).length;
  return hits / words.length > 0.12 || words.length <= 3;
}

// ---- Find a Lawyer: civilian-only interactive flow. Replaces the feed area while active. ----
function FindLawyerFlow({ onClose }) {
  const [step, setStep] = useState('category'); // category -> describe -> location -> results
  const [category, setCategory] = useState('');
  const [caseText, setCaseText] = useState('');
  const [locationState, setLocationState] = useState('idle'); // idle -> asking -> granted -> denied
  const [locationLabel, setLocationLabel] = useState('');

  function requestLocation() {
    setLocationState('asking');
    if (!navigator.geolocation) { setLocationState('denied'); return; }
    navigator.geolocation.getCurrentPosition(
      () => { setLocationLabel('Harare, Zimbabwe (approximate)'); setLocationState('granted'); setTimeout(() => setStep('results'), 500); },
      () => setLocationState('denied'),
      { timeout: 6000 }
    );
  }

  const sorted = useMemo(() => [...mockLawyers].sort((a, b) => (b.sponsored === a.sponsored ? b.rating - a.rating : b.sponsored - a.sponsored)), []);

  return <div className={styles.findLawyer}>
    <div className={styles.findLawyerHead}><b>👤 Find a Lawyer</b><button onClick={onClose} className={styles.closeX}>×</button></div>

    {step === 'category' && <div className={styles.flStep}>
      <p>What kind of legal issue is this about?</p>
      <div className={styles.flChips}>{findLawyerCategories.map((c) => <button key={c} className={category === c ? styles.flChipActive : ''} onClick={() => { setCategory(c); setStep('describe'); }}>{c}</button>)}</div>
    </div>}

    {step === 'describe' && <div className={styles.flStep}>
      <p>Not sure, or want to add detail? Describe your case below.</p>
      <textarea rows={3} value={caseText} onChange={(e) => setCaseText(e.target.value)} placeholder="Briefly describe your situation..." />
      <div className={styles.flActions}><button className={styles.outline} onClick={() => setStep('category')}>← Back</button><button className={styles.gold} onClick={() => setStep('location')}>Continue</button></div>
    </div>}

    {step === 'location' && <div className={styles.flStep}>
      {locationState === 'idle' && <><p>Allow location access so we can find lawyers near you?</p><div className={styles.flActions}><button className={styles.outline} onClick={() => setStep('results')}>Skip for now</button><button className={styles.gold} onClick={requestLocation}>Allow location</button></div></>}
      {locationState === 'asking' && <p>Requesting your location…</p>}
      {locationState === 'denied' && <><p>Location access wasn't allowed. Please allow location access in your browser to find lawyers near you, or continue without it.</p><div className={styles.flActions}><button className={styles.outline} onClick={requestLocation}>Try again</button><button className={styles.gold} onClick={() => setStep('results')}>Continue anyway</button></div></>}
      {locationState === 'granted' && <p>Location detected: {locationLabel}. Finding lawyers…</p>}
    </div>}

    {step === 'results' && <div className={styles.flStep}>
      <p className={styles.muted2}>{category || 'General enquiry'}{locationLabel ? ' · ' + locationLabel : ''} — showing sponsored lawyers first, then by rating. No in-app messaging yet — contact lawyers directly.</p>
      <div className={styles.lawyerResults}>
        {sorted.map((l) => <div key={l.slug} className={styles.lawyerResultCard}>
          <div className={styles.av2} style={{ background: avatarColor(l.name) }}>{initials(l.name)}</div>
          <div className={styles.lrBody}>
            <div><b>{l.name}</b> {l.sponsored ? <span className={styles.badgeSponsored}>Sponsored</span> : <span className={styles.badgeRated}>★ {l.rating} rated</span>}</div>
            <span className={styles.muted2}>{l.area} · {l.location} · {l.experience}</span>
            <div className={styles.flActions} style={{ marginTop: 8 }}>
              <Link href={`/lawyers/${l.slug}`} className={styles.outline}>View profile</Link>
              <a href={`tel:${l.phone}`} className={styles.outline}>📞 Call</a>
              <a href={`mailto:${l.email}`} className={styles.gold}>✉ Email</a>
            </div>
          </div>
        </div>)}
      </div>
    </div>}
  </div>;
}

// ---- Mentorship: student-only, replaces Tools. Search + join-confirmation + mock group view. ----
function MentorshipSection({ onOpenGroup }) {
  const [q, setQ] = useState('');
  const seen = new Set();
  const list = mentorship.filter((m) => !q.trim() || m.title.toLowerCase().includes(q.toLowerCase()) || m.mentor.toLowerCase().includes(q.toLowerCase()));
  return <div className={styles.mentorList}>
    <input className={styles.mentorSearch} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search mentorship programmes…" />
    {list.filter((m) => (seen.has(m.title) ? false : (seen.add(m.title), true))).map((m) => (
      <button key={m.id} className={styles.mentorItem} onClick={() => onOpenGroup(m)}>
        <b>{m.title}</b><span>{m.mentor} · {m.weeks} weeks · {m.free ? 'Free' : 'Paid'}</span>
      </button>
    ))}
  </div>;
}
function MentorshipConfirm({ programme, onJoin, onCancel }) {
  return <div className={styles.mentorConfirmBackdrop} onClick={onCancel}>
    <div className={styles.mentorConfirm} onClick={(e) => e.stopPropagation()}>
      <h3>{programme.title}</h3>
      <p className={styles.muted2}>With {programme.mentor} · {programme.weeks} weeks · {programme.students} students · {programme.free ? 'Free programme' : 'Paid programme'}</p>
      <p style={{ fontSize: 13, lineHeight: 1.6 }}>{programme.description}</p>
      <b style={{ fontSize: 12 }}>What you'll learn</b>
      <ul className={styles.topicList}>{programme.topics.map((t) => <li key={t}>{t}</li>)}</ul>
      <div className={styles.flActions}><button className={styles.outline} onClick={onCancel}>Cancel</button><button className={styles.gold} onClick={onJoin}>Join programme</button></div>
    </div>
  </div>;
}
function MentorshipGroup({ programme, onLeave }) {
  return <div className={styles.groupView}>
    <div className={styles.groupHead}><div><b>{programme.title}</b><span className={styles.muted2}> · {programme.students} students · {programme.mentor}</span></div><button className={styles.outline} onClick={onLeave}>← Back</button></div>
    <div className={styles.groupBody}>
      <div className={styles.groupFeed}>
        {mentorshipMessages.map((m, i) => <div key={i} className={styles.groupMsg}>
          <div className={styles.av2} style={{ background: avatarColor(m.author) }}>{initials(m.author)}</div>
          <div><b>{m.author}</b> {m.role === 'lawyer' && <span className={styles.starsStudent2}>★★★</span>} <span className={styles.muted2}>{m.time}</span><p>{m.text}</p></div>
        </div>)}
      </div>
      <aside className={styles.groupSide}>
        <b style={{ fontSize: 12 }}>Materials</b>
        {mentorshipMaterials.map((mat) => <div key={mat.title} className={styles.materialRow}>📄 {mat.title}<span>{mat.type}</span></div>)}
        <div className={styles.reminderBox}>🔔 Reminder: next session in 2 days</div>
      </aside>
    </div>
    <div className={styles.groupComposer}><input placeholder={`Write a message in ${programme.title}...`} /><button className={styles.gold}>Send</button></div>
  </div>;
}

function HomeInner() {
  const params = useSearchParams();
  // Prototype-only role preview - real auth will replace this later, this is just so the
  // one homepage component's different views can be reviewed without a login system yet.
  const role = params.get('view') || 'visitor'; // visitor | civilian | student

  const [community, setCommunity] = useState('all');
  const [search, setSearch] = useState('');
  const [menu, setMenu] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(true);
  const [communitiesOpen, setCommunitiesOpen] = useState(true);
  const [liked, setLiked] = useState([]);
  const [saved, setSaved] = useState([]);
  const [posts, setPosts] = useState(initialPosts);
  const [draft, setDraft] = useState('');
  const [flowStep, setFlowStep] = useState('idle');
  const [suggestedLawyer, setSuggestedLawyer] = useState(null);
  const [newPostId, setNewPostId] = useState(null);
  const [showFindLawyer, setShowFindLawyer] = useState(false);
  const [briefAnswer, setBriefAnswer] = useState(null);
  const [activeProgramme, setActiveProgramme] = useState(null);
  const [confirmProgramme, setConfirmProgramme] = useState(null);
  const [joinedGroup, setJoinedGroup] = useState(null);

  const visible = useMemo(() => posts.filter((p) => {
    const inCommunity = community === 'all' || p.community === community;
    const q = search.trim().toLowerCase();
    const civilianOk = role !== 'civilian' || p.community !== undefined; // civilians only see civilian-relevant posts (all are civilian-relevant in this mock set)
    return inCommunity && civilianOk && (!q || `${p.title} ${p.text}`.toLowerCase().includes(q));
  }), [posts, community, search, role]);

  const toggle = (setter, id) => setter((v) => (v.includes(id) ? v.filter((x) => x !== id) : [...v, id]));

  function submitPost() {
    if (!draft.trim() || flowStep !== 'idle') return;
    if (role === 'student') {
      // Brief chatbot-only mode: no lawyer suggestion, short canned answer, English-only gate.
      if (!looksLikeEnglish(draft)) { setBriefAnswer({ text: "Sorry, I can only respond in English right now.", ok: false }); return; }
      setFlowStep('posting');
      setTimeout(() => { setBriefAnswer({ text: 'Generally, this depends on the specific facts and the applicable law. Please check the relevant statute or case law for the exact position.', ok: true }); setFlowStep('idle'); }, 800);
      return;
    }
    setFlowStep('posting');
    setTimeout(() => setFlowStep('analyzing'), 700);
    setTimeout(() => setFlowStep('suggesting'), 1600);
    setTimeout(() => { setSuggestedLawyer(mockLawyers[Math.floor(Math.random() * mockLawyers.length)]); setFlowStep('suggested'); }, 2500);
  }
  function confirmPost() {
    const id = Date.now();
    setPosts((p) => [{ id, user: 'You', role: role === 'student' ? 'student' : 'public', community: 'workplace', time: 'just now', title: draft.slice(0, 90), text: draft, replies: 0, views: 1, likes: 0 }, ...p]);
    setNewPostId(id);
    setDraft(''); setFlowStep('idle'); setSuggestedLawyer(null); setBriefAnswer(null);
    setTimeout(() => setNewPostId(null), 1500);
  }

  if (joinedGroup) return <div className={styles.app}><TopBar role={role} menu={menu} setMenu={setMenu} search={search} setSearch={setSearch} /><div className={styles.layout} style={{ gridTemplateColumns: '1fr' }}><MentorshipGroup programme={joinedGroup} onLeave={() => setJoinedGroup(null)} /></div></div>;

  return <div className={styles.app}>
    <TopBar role={role} menu={menu} setMenu={setMenu} search={search} setSearch={setSearch} />
    <div className={styles.layout}>
      <aside className={`${styles.sidebar} ${menu ? styles.sidebarOpen : ''}`}>
        <a className={styles.navLink} href="/" title="Home"><span className={styles.iconSwatch} style={{ background: '#eef2ff', color: '#3b82f6' }}>⌂</span> Home</a>
        {role !== 'civilian' && <a className={styles.navLink} href="/chat" title="AI Legal Chatbot"><span className={styles.iconSwatch} style={{ background: '#ecfdf5', color: '#10b981' }}>✦</span> AI Chatbot</a>}

        {role === 'student' ? <>
          <button className={styles.sectionToggle} onClick={() => setToolsOpen((v) => !v)}>Mentorship Programs <span className={`${styles.arrow} ${toolsOpen ? styles.arrowOpen : ''}`}>›</span></button>
          <div className={`${styles.subLinks} ${toolsOpen ? styles.subLinksOpen : ''}`} style={{ maxHeight: toolsOpen ? 400 : 0 }}>
            <MentorshipSection onOpenGroup={(m) => setConfirmProgramme(m)} />
          </div>
        </> : <>
          <button className={styles.sectionToggle} onClick={() => setToolsOpen((v) => !v)}>Tools <span className={`${styles.arrow} ${toolsOpen ? styles.arrowOpen : ''}`}>›</span></button>
          <div className={`${styles.subLinks} ${toolsOpen ? styles.subLinksOpen : ''}`}>
            {tools.map((t) => <button key={t.name} className={styles.subLink} title={t.desc} onClick={() => alert(t.name + ' is a frontend demo for now.')}>
              <span className={styles.iconSwatch} style={{ width: 20, height: 20, fontSize: 11, background: t.color + '1a', color: t.color }}>{t.icon}</span> {t.name}
            </button>)}
          </div>
        </>}

        <div className={styles.divider} />

        {role === 'civilian' ? <>
          <button className={styles.sectionToggle} onClick={() => setCommunitiesOpen((v) => !v)}>Featured Lawyers <span className={`${styles.arrow} ${communitiesOpen ? styles.arrowOpen : ''}`}>›</span></button>
          <div className={`${styles.subLinks} ${communitiesOpen ? styles.subLinksOpen : ''}`} style={{ maxHeight: communitiesOpen ? 400 : 0 }}>
            {[...mockLawyers].sort((a, b) => (b.sponsored === a.sponsored ? b.rating - a.rating : b.sponsored - a.sponsored)).map((l) => (
              <Link key={l.slug} href={`/lawyers/${l.slug}`} className={styles.communityRow}>
                <span className={styles.av2} style={{ width: 20, height: 20, fontSize: 9, background: avatarColor(l.name) }}>{initials(l.name)}</span>
                {l.name} {l.sponsored ? <span className={styles.badgeSponsoredSm}>Sponsored</span> : <span className={styles.badgeRatedSm}>★ {l.rating}</span>}
              </Link>
            ))}
          </div>
        </> : <>
          <button className={styles.sectionToggle} onClick={() => setCommunitiesOpen((v) => !v)}>Communities <span className={`${styles.arrow} ${communitiesOpen ? styles.arrowOpen : ''}`}>›</span></button>
          <div className={`${styles.subLinks} ${communitiesOpen ? styles.subLinksOpen : ''}`} style={{ maxHeight: communitiesOpen ? 400 : 0 }}>
            <button className={styles.communityRow} onClick={() => { setCommunity('all'); setMenu(false); }}><span className={styles.communityDot} style={{ background: '#a39c8c' }} /> All communities</button>
            {communities.map((c) => <button key={c.key} className={styles.communityRow} onClick={() => { setCommunity(c.key); setMenu(false); }}><span className={styles.communityDot} style={{ background: c.color }} /> {c.name}</button>)}
          </div>
        </>}

        <div className={styles.sectionToggle} style={{ cursor: 'default' }}>Popular</div>
        {trending.slice(0, 3).map((t) => <a key={t.title} href="#" className={styles.popularItem}><b>{t.title}</b><span>{t.likes} likes</span></a>)}
      </aside>

      <main className={styles.main}>
        {showFindLawyer && role === 'civilian' ? <FindLawyerFlow onClose={() => setShowFindLawyer(false)} /> : <>
          <div className={styles.composer}>
            <textarea rows={2} placeholder={role === 'student' ? 'Ask a quick legal question…' : 'Ask a legal question or start a discussion...'} value={draft} onChange={(e) => setDraft(e.target.value)} disabled={flowStep !== 'idle'} />
            <div className={styles.composerFoot}>
              {flowStep === 'idle' && role !== 'student' && <span className={styles.composerHint}>Posting requires an account — you'll be asked to log in.</span>}
              {flowStep === 'idle' && role === 'student' && <span className={styles.composerHint}>✦ Quick answers only — <Link href="/chat">use the full chatbot</Link> for detailed help.</span>}
              {flowStep === 'posting' && <span className={styles.composerStatus}><span className={styles.dotPulse} /> {role === 'student' ? 'Thinking…' : 'Posting your question…'}</span>}
              {flowStep === 'analyzing' && <span className={styles.composerStatus}><span className={styles.dotPulse} /> AI is reviewing your question…</span>}
              {flowStep === 'suggesting' && <span className={styles.composerStatus}><span className={styles.dotPulse} /> Finding a lawyer who can help…</span>}
              {flowStep === 'suggested' && <span className={styles.composerStatus}>Ready to post</span>}
              <div style={{ display: 'flex', gap: 8 }}>
                {role === 'civilian' && <button className={styles.outline} onClick={() => setShowFindLawyer(true)}>👤 Find a Lawyer</button>}
                <button className={styles.goldBtn} onClick={flowStep === 'suggested' ? confirmPost : submitPost} disabled={!draft.trim() || (flowStep !== 'idle' && flowStep !== 'suggested')}>
                  {role === 'student' ? 'Ask' : flowStep === 'suggested' ? 'Confirm & Post' : 'Post'}
                </button>
              </div>
            </div>
            {role === 'student' && briefAnswer && <div className={briefAnswer.ok ? styles.briefAnswer : styles.briefAnswerError}>
              <span className={styles.iconSwatch} style={{ width: 20, height: 20, fontSize: 11, background: '#ecfdf5', color: '#10b981' }}>✦</span>
              <p>{briefAnswer.text} {briefAnswer.ok && <Link href="/chat">For more detail, go to the chatbot →</Link>}</p>
            </div>}
            {role !== 'student' && flowStep === 'suggested' && suggestedLawyer && <div className={styles.lawyerSuggest}>
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
        </>}
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
    {confirmProgramme && <MentorshipConfirm programme={confirmProgramme} onCancel={() => setConfirmProgramme(null)} onJoin={() => { setJoinedGroup(confirmProgramme); setConfirmProgramme(null); }} />}
    <footer className={styles.footer}><span>© 2026 LAFRE</span><span>Legal community · Professional networking · AI-assisted tools</span><span>General information only · Not legal advice</span></footer>
  </div>;
}

function TopBar({ role, menu, setMenu, search, setSearch }) {
  return <header className={styles.topbar}>
    <div className={styles.topInner}>
      <a href="/" className={styles.brand}><span className={styles.mark}>⚖</span><span><b>LAFRE</b><small>LAW · COMMUNITY · SOLUTIONS</small></span></a>
      <button className={styles.menu} onClick={() => setMenu(!menu)}>☰</button>
      <label className={styles.search}><span>⌕</span><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search discussions, lawyers, topics..." /></label>
      <div className={styles.topActions}>
        {/* Prototype-only role preview switch - stands in for real auth for now */}
        <div className={styles.roleSwitch}>
          <a href="?view=visitor" className={role === 'visitor' ? styles.roleActive : ''}>Visitor</a>
          <a href="?view=civilian" className={role === 'civilian' ? styles.roleActive : ''}>Civilian</a>
          <a href="?view=student" className={role === 'student' ? styles.roleActive : ''}>Student</a>
        </div>
        <a href="/login" className={styles.login}>Log in</a>
        <a href="/register" className={styles.signup}>Sign up</a>
      </div>
    </div>
  </header>;
}

export default function LafreForumHome() {
  return <Suspense fallback={<div style={{ padding: 40 }}>Loading…</div>}><HomeInner /></Suspense>;
}
