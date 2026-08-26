'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiFetch, clearAuth, getApiBase, getProfile, getToken } from '../lib/api';


function formatDate(value) { try { return new Date(value).toLocaleDateString([], { month: 'short', day: 'numeric' }); } catch { return ''; } }
function profileInitial(profile) { return (profile?.full_name || profile?.email || 'L').slice(0, 1).toUpperCase(); }
function displayName(profile) { return profile?.full_name || profile?.name || profile?.email || 'Student'; }
function plainText(value) { return String(value || '').replace(/^#{1,6}\s+/gm, '').replace(/\*\*/g, '').replace(/`/g, '').replace(/\[(?:K|D|S)\d+\]/g, '').trim(); }
function inlineFormat(text) {
  const parts = String(text || '').split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (/^`[^`]+`$/.test(part)) return <code key={i}>{part.slice(1, -1)}</code>;
    return <span key={i}>{part}</span>;
  });
}
function parseTable(lines, startIndex) {
  const header = lines[startIndex]; const divider = lines[startIndex + 1];
  if (!header?.includes('|') || !/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(divider || '')) return null;
  const split = (line) => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
  const headers = split(header); const rows = []; let i = startIndex + 2;
  while (i < lines.length && lines[i].includes('|') && lines[i].trim()) { rows.push(split(lines[i])); i += 1; }
  return { headers, rows, nextIndex: i };
}
function MarkdownBlock({ text = '' }) {
  const cleanText = String(text || '').replace(/\\n/g, '\n').replace(/\r\n/g, '\n').replace(/^\s*---+\s*$/gm, '');
  const lines = cleanText.split('\n'); const blocks = []; let paragraph = []; let list = []; let ordered = false;
  const flushParagraph = () => { if (paragraph.length) { blocks.push(<p key={`p-${blocks.length}`}>{inlineFormat(paragraph.join(' '))}</p>); paragraph = []; } };
  const flushList = () => { if (list.length) { const Tag = ordered ? 'ol' : 'ul'; blocks.push(<Tag key={`l-${blocks.length}`}>{list.map((item, idx) => <li key={idx}>{inlineFormat(item)}</li>)}</Tag>); list = []; ordered = false; } };
  for (let i = 0; i < lines.length; i += 1) {
    const line = (lines[i] || '').trim(); if (!line) { flushParagraph(); flushList(); continue; }
    const table = parseTable(lines, i); if (table) { flushParagraph(); flushList(); blocks.push(<div className="study-table-wrap" key={`t-${blocks.length}`}><table className="study-table"><thead><tr>{table.headers.map((h, idx) => <th key={idx}>{inlineFormat(h)}</th>)}</tr></thead><tbody>{table.rows.map((row, ridx) => <tr key={ridx}>{table.headers.map((_, cidx) => <td key={cidx}>{inlineFormat(row[cidx] || '')}</td>)}</tr>)}</tbody></table></div>); i = table.nextIndex - 1; continue; }
    if (/^#{1,4}\s+/.test(line)) { flushParagraph(); flushList(); const level = line.match(/^#+/)[0].length; const clean = line.replace(/^#{1,4}\s+/, ''); const Tag = level === 1 ? 'h2' : level === 2 ? 'h3' : 'h4'; blocks.push(<Tag key={`h-${blocks.length}`}>{inlineFormat(clean)}</Tag>); continue; }
    if (/^>\s?/.test(line)) { flushParagraph(); flushList(); blocks.push(<blockquote key={`q-${blocks.length}`}>{inlineFormat(line.replace(/^>\s?/, ''))}</blockquote>); continue; }
    if (/^[-*•]\s+\[[ xX]\]\s+/.test(line)) { flushParagraph(); if (ordered) flushList(); const checked = /\[[xX]\]/.test(line); const label = line.replace(/^[-*•]\s+\[[ xX]\]\s+/, ''); blocks.push(<div className="study-check-item" key={`c-${blocks.length}`}><span className={`study-check-box${checked ? ' checked' : ''}`} aria-hidden="true">{checked ? '✓' : ''}</span><span>{inlineFormat(label)}</span></div>); continue; }
    if (/^[-*•]\s+/.test(line)) { flushParagraph(); if (ordered) flushList(); list.push(line.replace(/^[-*•]\s+/, '')); ordered = false; continue; }
    if (/^\d+[.)]\s+/.test(line)) { flushParagraph(); if (list.length && !ordered) flushList(); list.push(line.replace(/^\d+[.)]\s+/, '')); ordered = true; continue; }
    paragraph.push(line);
  }
  flushParagraph(); flushList(); return <div className="study-markdown">{blocks}</div>;
}
async function fetchProtectedFile(apiPath, { download = false, filename = 'lafre-document' } = {}) {
  if (!apiPath) return; const url = apiPath.startsWith('http') ? apiPath : `${getApiBase()}${apiPath.replace(/^\/api/, '')}`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
  if (!res.ok) throw new Error('Could not open the document. Sign in and try again.');
  const blob = await res.blob(); const blobUrl = URL.createObjectURL(blob);
  if (download) { const a = document.createElement('a'); a.href = blobUrl; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(blobUrl), 2500); }
  else { window.open(blobUrl, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(blobUrl), 60000); }
}
function LoadingCard({ label }) { return <div className="study-loading"><span /><div><b>LAFRE is working</b><p>{label || 'Getting started…'}</p></div></div>; }
function ErrorCard({ message, debug, onRetry, loginRequired }) {
  return <div className="study-error"><strong>{loginRequired ? 'Sign in to continue' : 'Something went wrong'}</strong><p>{message || 'We could not complete your request. Please try again.'}</p>{debug ? <details className="auth-debug"><summary>Debug details</summary>{debug}</details> : null}{loginRequired ? <a className="lafre-brown-btn" href="/login">Sign in</a> : <button type="button" onClick={onRetry}>Try again</button>}</div>;
}
function DocumentCards({ docs = [], onSource }) {
  const clean = (docs || []).filter((d) => d && d.title); if (!clean.length) return null;
  return <section className="study-library-results"><div className="study-section-label">Library results · {clean.length} document{clean.length === 1 ? '' : 's'}</div><div className="study-result-list">{clean.slice(0, 8).map((doc, idx) => <article className="study-result-card" key={`${doc.id}-${idx}`} onClick={() => onSource?.(doc)}><div className="study-result-icon">▤</div><div className="study-result-body"><strong>{plainText(doc.title)}</strong><em>{plainText(doc.kind || 'Legal material')}</em><p>{plainText(doc.reason || doc.excerpt || 'Relevant study material').slice(0, 280)}</p>{doc.pages ? <small>{plainText(doc.pages)}</small> : null}</div><div className="study-result-actions">{doc.open_url && doc.can_open !== false ? <button type="button" onClick={(e) => { e.stopPropagation(); fetchProtectedFile(doc.open_url, { filename: doc.download_name || doc.title }).catch(alert); }}>View</button> : <button type="button" onClick={(e) => { e.stopPropagation(); onSource?.(doc); }}>Details</button>}</div></article>)}</div></section>;
}
function SourceBadges({ sources = [], onPick }) { const clean = (sources || []).filter((s) => s && s.title && s.kind !== 'error'); if (!clean.length) return null; return <div className="study-source-strip"><span>Sources</span>{clean.slice(0, 8).map((source, idx) => <button key={`${source.id}-${idx}`} type="button" onClick={() => onPick(source)}>{plainText(source.title)}</button>)}</div>; }
function CitationCards({ cards = [] }) {
  const [copiedId, setCopiedId] = useState(null);
  if (!cards.length) return null;
  const copy = async (text, id) => {
    try { await navigator.clipboard.writeText(text); setCopiedId(id); setTimeout(() => setCopiedId((c) => (c === id ? null : c)), 1500); } catch { /* clipboard unavailable, ignore */ }
  };
  return <div className="study-citation-cards">
    <div className="study-citation-cards-head"><b>📎 Citation cards</b><span>Tap to copy</span></div>
    {cards.map((c, idx) => <div className="study-citation-card" key={idx}>
      {c.phrase ? <p className="study-citation-phrase">"{c.phrase}"</p> : null}
      <button type="button" className="study-citation-line" onClick={() => copy(c.in_text, `${idx}-in`)}>
        <span className="study-citation-label">In-text</span><span>{c.in_text}</span><span className="study-citation-copy">{copiedId === `${idx}-in` ? 'Copied' : 'Copy'}</span>
      </button>
      <button type="button" className="study-citation-line" onClick={() => copy(c.full_reference, `${idx}-full`)}>
        <span className="study-citation-label">Reference</span><span>{c.full_reference}</span><span className="study-citation-copy">{copiedId === `${idx}-full` ? 'Copied' : 'Copy'}</span>
      </button>
    </div>)}
  </div>;
}
function FlashcardsWindow({ cards = [], title = 'Flashcards', onSave }) {
  const [flipped, setFlipped] = useState({}); const [saving, setSaving] = useState(false); const [saved, setSaved] = useState(false);
  const clean = (cards || []).filter((c) => c.front && c.back).slice(0, 12); if (!clean.length) return null;
  async function saveCards() { if (!onSave || saving || saved) return; setSaving(true); try { await onSave(clean, title); setSaved(true); } finally { setSaving(false); } }
  return <section className="study-flashcards"><div className="study-section-label">Flashcards</div><h2>{plainText(title)}</h2><div className="study-card-stack">{clean.map((card, idx) => { const isBack = Boolean(flipped[idx]); return <article className={`study-flash-card ${isBack ? 'is-back' : ''}`} key={`${card.front}-${idx}`}><div className="study-flash-meta"><span>Card {idx + 1} / {isBack ? 'Answer' : 'Question'}</span><button type="button" onClick={() => setFlipped((old) => ({ ...old, [idx]: !old[idx] }))}>↻ Flip</button></div><p>{plainText(isBack ? card.back : card.front)}</p>{card.topic ? <small>{plainText(card.topic)}</small> : null}</article>; })}</div><div className="study-flash-save"><button type="button" onClick={saveCards} disabled={saving || saved}>{saved ? 'Saved to library' : saving ? 'Saving...' : 'Save flashcards'}</button></div></section>;
}
function SourcePanel({ sources, onClose }) {
  const [activeId, setActiveId] = useState(null);
  useEffect(() => { setActiveId(null); }, [sources]);
  if (!sources || !sources.length) return null;
  const active = sources.find((s) => s.id === activeId) || null;
  return <aside className="study-source-panel">
    <div className="source-panel-head"><strong>{active ? plainText(active.title) : `Sources (${sources.length})`}</strong><button type="button" className="source-panel-close" onClick={active ? () => setActiveId(null) : onClose}>{active ? '← Back' : '×'}</button></div>
    {!active
      ? <ul className="source-panel-list">{sources.map((s, idx) => <li key={`${s.id}-${idx}`}><button type="button" onClick={() => setActiveId(s.id)}>
          <span className="source-panel-list-title">{plainText(s.title)}</span>
          <small>{plainText(s.kind || 'Source')}</small>
          {s.relevance ? <p className="source-panel-list-relevance">{plainText(s.relevance)}</p> : null}
        </button></li>)}</ul>
      : <div className="source-panel-detail">
          <div className="source-panel-meta"><span className="source-panel-chip">{plainText(active.kind || 'Source')}</span>{active.pages ? <span className="source-panel-chip">p. {plainText(active.pages)}</span> : null}<span className="source-panel-chip">{active.can_open ? 'Reference source' : 'Source note'}</span></div>
          {active.relevance ? <div className="source-readable-relevance"><b>Why this was used</b><p>{plainText(active.relevance)}</p></div> : null}
          {active.excerpt ? <div className="source-readable-extract"><b>Relevant extract</b><p>{plainText(active.excerpt)}</p></div> : null}
          <div className="source-panel-actions">{active.open_url && active.can_open !== false ? <button type="button" onClick={() => fetchProtectedFile(active.open_url, { filename: active.download_name || active.title }).catch(alert)}>View reference</button> : null}</div>
        </div>}
  </aside>;
}
function dedupeSources(list) {
  const seen = new Set(); const out = [];
  for (const s of list || []) { if (!s || !s.title) continue; const key = s.id || s.title; if (seen.has(key)) continue; seen.add(key); out.push(s); }
  return out;
}
// Sources are no longer dumped inline under every answer (that was the "sources on every
// question" complaint) - they're retrieved for grounding but only surfaced via this small
// toggle, which opens SourcePanel as a click-through library/reader view instead.
function AssistantMessage({ message, onSource, onAction, onRetry, onSaveFlashcards, isLast }) {
  const r = message.response || {};
  if (message.loading) return <div className="study-assistant"><LoadingCard label={message.statusLabel} /></div>;
  if (message.error) return <div className="study-assistant"><ErrorCard message={message.text} debug={message.debug} onRetry={onRetry} loginRequired={message.loginRequired} /></div>;
  const allSources = dedupeSources([...(r.source_badges || []), ...(r.documents || [])]);
  return <div className="study-assistant"><div className="study-answer">
    <MarkdownBlock text={message.text} />
    <FlashcardsWindow cards={r.flashcards || []} title={r.flashcard_title || r.title || 'Flashcards'} onSave={onSaveFlashcards} />
    <CitationCards cards={r.citation_cards || []} />
    {allSources.length ? <button type="button" className="study-sources-toggle" onClick={() => onSource(allSources)}>📚 Sources ({allSources.length})</button> : null}
    {r.legal_notice ? <p className="student-legal-notice">⚖ {r.legal_notice}</p> : null}
    {isLast && r.next_steps?.length ? <div className="study-next-actions">{r.next_steps.slice(0, 4).map((step) => <button key={step} type="button" onClick={() => onAction(step, r)}>{step}</button>)}</div> : null}
  </div></div>;
}
function UserMessage({ text, pending }) { return <div className={`study-user ${pending ? 'pending' : ''}`}><p>{text}</p></div>; }

function StudentChatContent() {
  const searchParams = useSearchParams();
  const [profile, setProfile] = useState(null); const [mounted, setMounted] = useState(false); const [sidebarOpen, setSidebarOpen] = useState(false); const [chatId, setChatId] = useState(null); const [chatTitle, setChatTitle] = useState('New chat'); const [chats, setChats] = useState([]); const [chatSearch, setChatSearch] = useState(''); const [messages, setMessages] = useState([]); const [prompt, setPrompt] = useState(''); const [loading, setLoading] = useState(false); const [sourcePanel, setSourcePanel] = useState(null); const [lastPrompt, setLastPrompt] = useState(''); const [mode, setMode] = useState('chat'); const [chatMenuOpen, setChatMenuOpen] = useState(false); const answerStyle = 'balanced'; const bottomRef = useRef(null);
  useEffect(() => { setMounted(true); setProfile(getProfile()); loadChats(); }, []);
  useEffect(() => { const id = searchParams.get('chat'); const q = searchParams.get('q'); if (id) openChat(id); else if (q) setPrompt(q); }, [searchParams]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, loading]);
  async function loadChats() { try { const res = await apiFetch('/students/chats/'); setChats(res.chats || []); } catch { setChats([]); } }
  async function openChat(id) { try { const res = await apiFetch(`/students/chats/${id}/`); const chat = res.chat || {}; setChatId(chat.id); setChatTitle(chat.title || 'Saved chat'); setMessages((chat.messages || []).map((m) => ({ role: m.role, text: m.role === 'assistant' ? (m.response?.markdown || m.text) : m.text, response: m.response || {}, created_at: m.created_at }))); setSidebarOpen(false); setSourcePanel(null); } catch {} }
  function newChat() { setChatId(null); setChatTitle('New chat'); setMessages([]); setSourcePanel(null); setPrompt(''); }
  function logout() { clearAuth(); window.location.href = '/login'; }
  function cleanTopicFromText(value) { let topic = String(value || '').trim(); topic = topic.replace(/^(explain|discuss|define|describe|compare)\s+/i, '').trim(); topic = topic.replace(/^(turn|make|create|find|show)\s+/i, '').trim(); topic = topic.replace(/\s+into\s+an?\s+exam[- ]style\s+answer.*$/i, '').trim(); topic = topic.replace(/^(flashcards|sources|documents)\s+(for|on|about)?\s*/i, '').trim(); if (topic.split(/\s+/).length > 10) topic = topic.split(/\s+/).slice(0, 8).join(' '); return topic || chatTitle || 'the previous answer'; }
  // next_steps chips are now full AI-generated questions (from the answer agent's
  // suggest_next tool), not short verb labels - they should be sent as-is. The old
  // keyword-template rewriting below is kept ONLY as a fallback for the empty-state starter
  // buttons, which are short labels, not full questions.
  // Suggestions now come from the AI itself (suggest_next), as full natural-language prompts -
  // there's no fixed/hardcoded label system to reinterpret anymore. Send exactly what was
  // suggested; string-splicing a topic onto it was the actual cause of garbled follow-ups.
  function buildFollowUp(action) {
    return String(action || '').trim();
  }
  async function renameChat() {
    if (!chatId) return;
    const next = window.prompt('Rename this chat', chatTitle === 'New chat' ? '' : chatTitle);
    if (!next || !next.trim()) return;
    try {
      const res = await apiFetch(`/students/chats/${chatId}/`, { method: 'PATCH', body: JSON.stringify({ title: next.trim() }) });
      setChatTitle(res.chat?.title || next.trim());
      await loadChats();
    } catch (err) { alert(err.message || 'Could not rename chat.'); }
  }
  async function deleteChat() {
    if (!chatId) return;
    if (!window.confirm('Delete this chat? This cannot be undone.')) return;
    try {
      await apiFetch(`/students/chats/${chatId}/`, { method: 'DELETE' });
      await loadChats();
      newChat();
    } catch (err) { alert(err.message || 'Could not delete chat.'); }
  }
  function copyChatLink() {
    try { navigator.clipboard.writeText(window.location.href); } catch { /* clipboard unavailable */ }
  }
  function viewForMode() { if (mode === 'legal_search') return 'documents'; if (mode === 'flashcards') return 'flashcards'; return 'auto'; }
  async function send(textArg, modeOverride) {
    const text = (textArg || prompt).trim(); if (!text || loading) return;
    const selectedMode = modeOverride || viewForMode();
    setPrompt(''); setLastPrompt(text); setLoading(true);
    setMessages((m) => [...m, { role: 'user', text, pending: true }, { role: 'assistant', loading: true, streaming: true, statusLabel: 'Getting started…', response: {} }]);
    // Real token streaming (SSE) instead of a blocking request + fake progress steps.
    // Falls back to the plain /ask/ endpoint if the stream can't be read for any reason.
    try {
      const headers = { 'Content-Type': 'application/json' };
      const token = getToken(); if (token) headers.Authorization = `Bearer ${token}`;
      const sessionId = (typeof window !== 'undefined' && localStorage.getItem('lafre_guest_session')) || '';
      if (sessionId) headers['X-Session-ID'] = sessionId;
      const res = await fetch(`${getApiBase()}/students/ask/stream/`, { method: 'POST', headers, body: JSON.stringify({ prompt: text, chat_id: chatId, mode: selectedMode, answer_style: answerStyle }) });
      if (!res.ok) {
        const ct = res.headers.get('content-type') || '';
        const data = ct.includes('application/json') ? await res.json().catch(() => ({})) : {};
        const err = new Error(data.message || data.detail || 'We could not complete your request.');
        err.status = res.status; err.payload = data; throw err;
      }
      const reader = res.body.getReader(); const decoder = new TextDecoder(); let buffer = ''; let acc = ''; let finalResponse = null; let finalChat = null;
      while (true) {
        const { value, done } = await reader.read(); if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n'); buffer = events.pop();
        for (const raw of events) {
          const line = raw.split('\n').find((l) => l.startsWith('data: ')); if (!line) continue;
          const evt = JSON.parse(line.slice(6));
          if (evt.type === 'meta') { /* meta.payload holds everything except markdown; used once 'done' arrives */ }
          else if (evt.type === 'status') { setMessages((m) => { const copy = [...m]; const last = copy[copy.length - 1]; if (last?.loading) copy[copy.length - 1] = { ...last, statusLabel: evt.text }; return copy; }); }
          else if (evt.type === 'token') { acc += evt.text; setMessages((m) => { const copy = [...m]; copy[copy.length - 1] = { role: 'assistant', loading: false, streaming: true, text: acc, response: {} }; return copy; }); }
          else if (evt.type === 'done') { finalResponse = evt.payload || {}; finalChat = finalResponse.chat || null; }
          else if (evt.type === 'error') { throw new Error(evt.message || 'The study assistant could not produce an answer.'); }
        }
      }
      const response = finalResponse || {}; const chatIdFromStream = finalChat?.id || response.chat_id;
      setChatId(chatIdFromStream || chatId); if (finalChat?.title) setChatTitle(finalChat.title);
      setMessages((m) => [...m.slice(0, -2), { role: 'user', text }, { role: 'assistant', text: response.markdown || acc || 'No response was returned.', response }]);
      await loadChats();
    } catch (err) {
      // Fall back to the non-streaming endpoint once before giving up, in case the
      // network/proxy doesn't support SSE (some corporate proxies buffer it).
      try {
        const res = await apiFetch('/students/ask/', { method: 'POST', body: JSON.stringify({ prompt: text, chat_id: chatId, mode: selectedMode, answer_style: answerStyle }) });
        const response = res.response || {};
        setChatId(res.chat_id || chatId); if (res.chat?.title) setChatTitle(res.chat.title);
        setMessages((m) => [...m.slice(0, -2), { role: 'user', text }, { role: 'assistant', text: response.markdown || 'No response was returned.', response }]);
        await loadChats();
      } catch (err2) {
        const loginRequired = err2.status === 401 && err2.payload?.mode === 'login_required';
        setMessages((m) => [...m.slice(0, -2), { role: 'user', text }, { role: 'assistant', error: true, loginRequired, text: loginRequired ? 'You have used the three-message guest preview. Sign in to keep this chat and continue.' : (err2.message || 'We could not complete your request.'), debug: err2.debug || '' }]);
      }
    } finally { setLoading(false); }
  }
  async function saveFlashcards(cards, title = '') { await apiFetch('/students/flashcards/', { method: 'POST', body: JSON.stringify({ title: title || (chatTitle === 'New chat' ? 'Saved flashcards' : `${chatTitle} flashcards`), cards, chat_id: chatId }) }); }
  const name = mounted ? displayName(profile) : 'Student'; const shownChats = chats.filter((c) => !chatSearch || (c.title || '').toLowerCase().includes(chatSearch.toLowerCase())); const hasMessages = messages.length > 0; const canSend = mounted && prompt.trim().length > 0 && !loading; const isGuest = mounted && !(getToken() && profile);
  return <div className={`study-chat-page ${sidebarOpen ? 'drawer-open' : ''}`}>{sidebarOpen ? <button type="button" className="study-backdrop" onClick={() => setSidebarOpen(false)} aria-label="Close menu" /> : null}<aside className="study-drawer chat-drawer"><div className="study-drawer-head"><a className="study-brand" href="/chat"><span>⚖</span><strong>LAFRE</strong></a><button type="button" onClick={() => setSidebarOpen(false)}>×</button></div><button type="button" className="study-new-chat" onClick={newChat}>▣ New chat</button><label className="study-search"><input value={chatSearch} onChange={(e) => setChatSearch(e.target.value)} placeholder="Search chats" /></label><div className="study-recent-title">Recent chats</div><nav className="study-recent-list">{shownChats.length ? shownChats.slice(0, 18).map((c) => <button key={c.id} type="button" className={c.id === chatId ? 'active' : ''} onClick={() => openChat(c.id)}><span>{c.title}</span><small>{formatDate(c.updated_at)}</small></button>) : <p>No chats yet.</p>}</nav><div className="study-drawer-nav"><a href="/library">▭ Library</a><a href="/flashcards">◆ Flashcards</a>{isGuest ? null : <><a href="/usage">◔ Usage & messages</a><a href="/settings">⚙ Settings</a><button type="button" onClick={logout}>↳ Log out</button></>}</div><div className="study-drawer-profile">{isGuest ? <a href="/login" className="study-guest-login">↳ Sign in to save chats</a> : <><span>{profileInitial(profile)}</span><div><b>{name}</b><small>{profile?.email || 'student@lafre.demo'}</small></div></>}</div></aside><main className="study-chat-main"><header className="study-chat-header"><button type="button" onClick={() => setSidebarOpen(true)}>☰</button><a className="study-brand" href="/chat"><span>⚖</span><strong>LAFRE</strong></a>{hasMessages ? <h1>{chatTitle === 'New chat' ? 'Student Chat' : chatTitle}</h1> : null}{hasMessages && chatId ? <div className="study-more-wrap"><button type="button" className="study-more" onClick={() => setChatMenuOpen((v) => !v)} aria-label="Chat options">⋮</button>{chatMenuOpen ? <div className="study-more-menu" onMouseLeave={() => setChatMenuOpen(false)}><button type="button" onClick={() => { setChatMenuOpen(false); renameChat(); }}>✎ Rename chat</button><button type="button" onClick={() => { setChatMenuOpen(false); copyChatLink(); }}>⛓ Copy link</button><button type="button" className="danger" onClick={() => { setChatMenuOpen(false); deleteChat(); }}>🗑 Delete chat</button></div> : null}</div> : <span className="study-more-spacer" />}</header><section className={`study-chat-scroll ${hasMessages ? '' : 'empty'}`}>{!hasMessages ? <div className="study-empty"><div className="study-empty-logo">⚖<span>LAFRE</span></div><h1>What are we studying today?</h1><p>Ask a question, request a case brief, or generate flashcards.</p><form className="study-start-composer" onSubmit={(e) => { e.preventDefault(); send(); }}><textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="e.g. Explain the postal rule with examples..." rows={3} /><div><button type="submit" disabled={!canSend} aria-disabled={!canSend}>↵</button></div></form><div className="study-suggestions"><button onClick={() => { setMode('chat'); send('Compare offer vs invitation to treat', 'auto'); }}>Compare offer vs invitation to treat</button><button onClick={() => { setMode('chat'); send('Brief Donoghue v Stevenson', 'auto'); }}>Brief Donoghue v Stevenson</button><button onClick={() => { setMode('legal_search'); send('Summarise s.17 of the Sale of Goods Act', 'documents'); }}>Summarise s.17 of the Sale of Goods Act</button><button onClick={() => { setMode('flashcards'); send('Flashcards on the elements of a valid contract', 'flashcards'); }}>Flashcards on the elements of a valid contract</button></div></div> : <div className="study-message-column">{messages.map((m, idx) => m.role === 'user' ? <UserMessage key={idx} text={m.text} pending={m.pending} /> : <AssistantMessage key={idx} message={m} isLast={idx === messages.length - 1} onSource={setSourcePanel} onAction={(a) => send(buildFollowUp(a))} onRetry={() => send(lastPrompt)} onSaveFlashcards={saveFlashcards} />)}<div ref={bottomRef} /></div>}</section>{hasMessages ? <form className="study-bottom-composer" onSubmit={(e) => { e.preventDefault(); send(); }}><textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Ask anything about law..." rows={1} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }} /><button type="submit" disabled={!canSend} aria-disabled={!canSend}>↵</button></form> : null}</main><SourcePanel sources={sourcePanel} onClose={() => setSourcePanel(null)} /></div>;
}

export default function StudentChat() {
  return (
    <Suspense fallback={<div className="study-chat-page"><main className="study-chat-main"><section className="study-chat-scroll empty"><div className="study-empty"><div className="study-empty-logo">⚖<span>LAFRE</span></div><p>Loading student chat...</p></div></section></main></div>}>
      <StudentChatContent />
    </Suspense>
  );
}
