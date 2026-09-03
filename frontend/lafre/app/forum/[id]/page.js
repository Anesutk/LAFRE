'use client';
import {useState} from 'react';
import Link from 'next/link';
import LafreShell from '../../prototype/components/LafreShell';
import {mockApi,posts} from '../../prototype/mock-api';
import {Icon} from '../../prototype/components/icons';
import {RoleBadge} from '../../prototype/components/PostCard';
import Status from '../../prototype/components/Status';
import ui from '../../prototype/components/ui.module.css';

export default function QuestionPage({params}){
 const post=posts.find(p=>p.id===params.id)||posts[0]; const [reply,setReply]=useState(''); const [sent,setSent]=useState(false);
 return <LafreShell active="Forum"><div className={ui.shell}>
  <div className={ui.row} style={{marginBottom:14}}><Link href="/forum" className={ui.muted} style={{textDecoration:'none',fontWeight:800}}>← Forum</Link><Status/></div>
  <div className={ui.twoCol}><main>
   <article className={ui.panel+' '+ui.pad}><div className={ui.row}><div><span className={ui.tag}>{post.category}</span><span className={ui.muted} style={{fontSize:11,marginLeft:8}}>{post.time}</span></div><button className={ui.outlineBtn} style={{height:32,padding:'0 10px'}}><Icon name="flag" size={14}/> Report</button></div><h1 style={{fontSize:30,lineHeight:1.16,margin:'14px 0 10px'}}>{post.title}</h1><div className={ui.row} style={{justifyContent:'flex-start'}}><span className={ui.avatar}>{post.author[0]}</span><div><b>{post.author}</b><div className={ui.muted} style={{fontSize:11}}>Public user · Zimbabwe</div></div></div><p style={{fontSize:15,lineHeight:1.75,color:'#3f3d38',marginTop:18}}>{post.excerpt} This is prototype content representing the longer user question that will eventually come from the backend.</p><div className={ui.divider}/><div className={ui.metrics}><span>↑ {post.score}</span><span><Icon name="message"/> 18 responses</span><span><Icon name="share"/> Share</span><span><Icon name="bookmark"/> Save</span></div></article>
   <section style={{marginTop:16}} className={ui.panel+' '+ui.pad}><div className={ui.row}><h2 style={{fontSize:19,margin:0}}>Responses</h2><span className={ui.muted} style={{fontSize:12}}>Most helpful</span></div>
    {[['Tapiwa Moyo','lawyer','Based on the information shared, this appears to involve employment-law questions. A full review of the agreement and applicable law would be needed before giving specific advice.'],['Rudo K.','student','One thing worth checking is the wording of the signed agreement and any notice or probation clauses.'],['Brian Chikore','lawyer','A verified lawyer can review the documents and your timeline more carefully if you choose to request professional help.']].map((r,i)=><div key={i} className={ui.listItem}><div className={ui.row} style={{justifyContent:'flex-start'}}><span className={ui.avatar}>{r[0][0]}</span><div><b>{r[0]}</b> <RoleBadge role={r[1]} /><div className={ui.muted} style={{fontSize:11}}>Mock response · {i+1}h ago</div></div></div><p style={{margin:'10px 0 7px',fontSize:13,lineHeight:1.6}}>{r[2]}</p><div className={ui.metrics}><span>Like</span><span>Reply</span></div></div>)}
   </section>
   <section className={ui.panel+' '+ui.pad} style={{marginTop:16}}><div className={ui.eyebrow}>Join the discussion</div><textarea value={reply} onChange={e=>setReply(e.target.value)} placeholder="Log in to write a response..." style={{width:'100%',minHeight:90,border:'1px solid #dad6cd',borderRadius:8,padding:12,marginTop:9}}/><div className={ui.row} style={{marginTop:10}}><span className={ui.muted} style={{fontSize:11}}>{sent?'Mock API: response queued.':'Login required to reply.'}</span><button className={ui.goldBtn} onClick={()=>setSent(true)}>Post response</button></div></section>
  </main><aside><div className={ui.panel+' '+ui.pad}><div className={ui.eyebrow}>Need professional help?</div><h3 style={{fontSize:19,margin:'7px 0'}}>Move privately from discussion to a lawyer.</h3><p className={ui.muted} style={{fontSize:13,lineHeight:1.55}}>Create a legal-help request with the area of law, location and situation. Suitable verified lawyers can then express interest.</p><Link href="/legal-help" className={ui.goldBtn} style={{width:'100%'}}>Request Legal Help</Link></div></aside></div>
 </div></LafreShell>
}
