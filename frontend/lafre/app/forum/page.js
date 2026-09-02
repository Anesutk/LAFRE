'use client';
import {useMemo,useState} from 'react';
import Link from 'next/link';
import LafreShell from '../prototype/components/LafreShell';
import PostCard from '../prototype/components/PostCard';
import QuestionComposer from '../prototype/components/QuestionComposer';
import Status from '../prototype/components/Status';
import {posts} from '../prototype/mock-api';
import ui from '../prototype/components/ui.module.css';

export default function Forum(){
 const [tab,setTab]=useState('Latest'); const [q,setQ]=useState(''); const [showComposer,setShowComposer]=useState(false);
 const filtered=useMemo(()=>posts.filter(p=>(p.title+p.excerpt+p.category).toLowerCase().includes(q.toLowerCase())),[q]);
 return <LafreShell active="Forum"><div className={ui.shell}>
  <div className={ui.row}><div><div className={ui.eyebrow}>LAFRE forum</div><h1 className={ui.title}>Legal questions, real conversations.</h1><p className={ui.subtitle}>Browse public questions and discussions. Login is required to participate.</p></div><Status>Mock API</Status></div>
  <div className={ui.twoCol} style={{marginTop:24}}><section>
   <div className={ui.panel+' '+ui.pad} style={{marginBottom:14}}><div className={ui.row}><div style={{display:'flex',gap:8,flexWrap:'wrap'}}>{['Latest','Trending','Unanswered','Following'].map(x=><button key={x} onClick={()=>setTab(x)} className={x===tab?ui.goldBtn:ui.outlineBtn} style={{height:34,padding:'0 11px',fontSize:12}}>{x}</button>)}</div><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search this forum" style={{height:36,width:210,border:'1px solid #d9d5cc',borderRadius:7,padding:'0 10px'}}/></div></div>
   <div className={ui.panel}>{filtered.map(p=><PostCard key={p.id} post={p}/>)}{!filtered.length&&<div className={ui.empty}>No demo discussions match that search.</div>}</div>
  </section><aside>
    <button className={ui.goldBtn} style={{width:'100%',marginBottom:12}} onClick={()=>setShowComposer(!showComposer)}>{showComposer?'Close question form':'Ask a Question'}</button>
    {showComposer?<QuestionComposer/>:<div className={ui.panel+' '+ui.pad}><div className={ui.eyebrow}>Community rules</div><h3 style={{fontSize:18}}>Keep the forum useful.</h3><p className={ui.muted} style={{lineHeight:1.6,fontSize:13}}>Be respectful. Do not publish sensitive personal information. Student-only questions are reserved for verified lawyers.</p><div className={ui.divider}/><div className={ui.listItem}><b>Need a lawyer?</b><div className={ui.muted}>Use a structured legal-help request rather than posting private case details publicly.</div></div><Link href="/legal-help" className={ui.outlineBtn} style={{width:'100%',marginTop:12}}>View legal help</Link></div>}
  </aside></div>
 </div></LafreShell>
}
