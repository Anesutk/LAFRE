'use client';
import { useEffect, useState } from 'react';
import StudentShell from '../../components/StudentShell';
import { apiFetch } from '../../lib/api';

export default function Flashcards() {
  const [decks,setDecks]=useState([]);
  useEffect(()=>{apiFetch('/students/flashcards/').then(r=>setDecks(r.decks||[])).catch(()=>{})},[]);
  return <StudentShell active="library" title="Flashcards">
    <section className="warm-page-copy"><a href="/chat" className="warm-back">← Back to chat</a><h1>Flashcards</h1><p>Saved revision cards generated from chats and legal materials.</p></section>
    {decks.length===0 ? <section className="warm-empty-card"><h2>No saved flashcards yet</h2><p>Create flashcards inside chat, then save them here for revision.</p><a className="lafre-brown-btn" href="/chat">Go to chat</a></section> : <div className="study-card-stack">{decks.map(d=><section className="warm-account-card" key={d.id}><h2>{d.title}</h2>{d.cards.map((c,i)=><article className="study-flash-card" key={c.id}><div className="study-flash-meta"><span>Card {i+1}</span></div><p>{c.front}</p><small>{c.back}</small></article>)}</section>)}</div>}
  </StudentShell>;
}
