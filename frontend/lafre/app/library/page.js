'use client';

import { useEffect, useMemo, useState } from 'react';
import StudentShell from '../../components/StudentShell';
import { apiFetch, getApiBase, getToken } from '../../lib/api';

function formatSize(bytes) { if (!bytes) return '—'; if (bytes < 1024) return `${bytes} B`; if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`; return `${(bytes / 1024 / 1024).toFixed(1)} MB`; }
function formatDate(value) { try { return new Date(value).toLocaleDateString(); } catch { return '—'; } }
function fileKind(doc) { return String(doc.type || doc.title?.split('.').pop() || 'Document').toUpperCase(); }
async function fetchProtectedFile(apiPath, { download = false, filename = 'lafre-document' } = {}) {
  if (!apiPath) return;
  const url = apiPath.startsWith('http') ? apiPath : `${getApiBase()}${apiPath.replace(/^\/api/, '')}`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
  if (!res.ok) throw new Error('Could not open the document. Sign in and try again.');
  const blob = await res.blob(); const blobUrl = URL.createObjectURL(blob);
  if (download) { const a = document.createElement('a'); a.href = blobUrl; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(blobUrl), 2500); }
  else { window.open(blobUrl, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(blobUrl), 60000); }
}
function ErrorStrip({ err }) { if (!err) return null; return <div className="error-strip">{err.message || err}{err.debug ? <details className="auth-debug"><summary>Debug details</summary>{err.debug}</details> : null}</div>; }

export default function StudentLibrary() {
  const [docs, setDocs] = useState([]); const [file, setFile] = useState(null); const [uploading, setUploading] = useState(false); const [message, setMessage] = useState(''); const [error, setError] = useState(null);
  async function load() { try { const res = await apiFetch('/students/documents/'); setDocs(res.documents || []); } catch (err) { setError(err); } }
  useEffect(() => { load(); }, []);
  const sorted = useMemo(() => docs, [docs]);
  async function upload(e) { e?.preventDefault?.(); if (!file) { setError({ message: 'Choose a document first.' }); return; } setUploading(true); setError(null); setMessage(''); const form = new FormData(); form.append('file', file); form.append('title', file.name); try { await apiFetch('/students/assignment-upload/', { method: 'POST', body: form }); setFile(null); setMessage('Document uploaded successfully.'); await load(); } catch (err) { setError(err); } finally { setUploading(false); } }

  return <StudentShell active="library" title="Library">
    <section className="warm-page-copy"><a href="/chat" className="warm-back">← Back to chat</a><h1>Library</h1><p>Notes, cases, statutes, and lecture materials. Searched by the assistant when you ask questions.</p></section>
    <form onSubmit={upload} className="warm-upload-bar"><label>⇧ Upload documents<input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} /></label>{file ? <span>{file.name}</span> : null}{file ? <button disabled={uploading}>{uploading ? 'Uploading...' : 'Upload'}</button> : null}</form>
    {message ? <div className="success-strip">{message}</div> : null}<ErrorStrip err={error} />
    {sorted.length ? <div className="warm-document-list">{sorted.map((doc) => <article key={doc.id} className="warm-document-row"><div className="warm-doc-icon">{fileKind(doc).slice(0, 4)}</div><div><strong>{doc.title}</strong><p>{formatDate(doc.created_at)} · {formatSize(doc.size)}</p>{doc.excerpt ? <small>{doc.excerpt.slice(0, 180)}</small> : null}</div><div><button type="button" onClick={() => fetchProtectedFile(doc.open_url, { filename: doc.title }).catch((e) => setError(e))}>View</button><button type="button" onClick={() => { window.location.href = `/chat?q=${encodeURIComponent(`Use ${doc.title} in my answer`)}`; }}>Use in chat</button></div></article>)}</div> : <section className="warm-empty-card"><div>▤</div><h2>Your library is empty</h2><p>Upload notes, cases or statutes. The assistant will use them when you ask related questions.</p><label>⇧ Upload your first file<input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} /></label>{file ? <button type="button" onClick={upload} disabled={uploading}>{uploading ? 'Uploading...' : 'Upload selected file'}</button> : null}</section>}
  </StudentShell>;
}
