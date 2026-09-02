import Link from 'next/link';
import LafreShell from './prototype/components/LafreShell';
import PostCard from './prototype/components/PostCard';
import LawyerCard from './prototype/components/LawyerCard';
import Status from './prototype/components/Status';
import ui from './prototype/components/ui.module.css';
import {mockApi} from './prototype/mock-api';

export default async function Landing(){
 const [posts, lawyers]=await Promise.all([mockApi.getPosts(),mockApi.getLawyers()]);
 return <LafreShell active="Home">
   <div className={ui.shell}>
    <div className={ui.row} style={{marginBottom:20}}><Status/><span className={ui.muted} style={{fontSize:12}}>Public visitor view · prototype data</span></div>
    <section className={ui.panel} style={{padding:'42px 42px',display:'grid',gridTemplateColumns:'1.35fr .65fr',gap:28,alignItems:'center'}}>
      <div><div className={ui.eyebrow}>Legal community</div><h1 className={ui.title}>Ask. Discuss. Connect.</h1><p className={ui.subtitle}>A trusted place to understand legal issues, learn from the community, find verified lawyers and move from general information to professional help when you need it.</p><div className={ui.btnRow} style={{marginTop:20}}><Link href="/login" className={ui.goldBtn}>Ask a Question</Link><Link href="/lawyers" className={ui.outlineBtn}>Find a Lawyer</Link><Link href="/chat" className={ui.outlineBtn}>Open LAFRE Chatbot</Link></div></div>
      <div style={{borderLeft:'1px solid #e5e0d6',paddingLeft:28}}><div className={ui.eyebrow}>What visitors can do</div><div className={ui.listItem}><b>Read discussions</b><div className={ui.muted}>Browse public legal questions without logging in.</div></div><div className={ui.listItem}><b>Explore lawyers</b><div className={ui.muted}>Review verified professional profiles.</div></div><div className={ui.listItem}><b>Join the conversation</b><div className={ui.muted}>Log in to post, reply, like, connect or request help.</div></div></div>
    </section>
    <section style={{marginTop:28}}><div className={ui.row}><div><div className={ui.eyebrow}>Community</div><h2 style={{fontSize:23,margin:'5px 0'}}>Latest discussions</h2></div><Link href="/forum" className={ui.outlineBtn}>View forum</Link></div><div className={ui.twoCol} style={{marginTop:12}}><div className={ui.panel}>{posts.slice(0,4).map(p=><PostCard key={p.id} post={p}/>)}</div><div><div className={ui.panel+' '+ui.pad}><div className={ui.row}><h3 style={{margin:0,fontSize:17}}>AI legal tools</h3><Link href="/ai-tools" className={ui.goldText} style={{fontWeight:850,fontSize:12}}>View all →</Link></div><p className={ui.muted} style={{fontSize:12,lineHeight:1.55}}>Useful assistive tools for explanations, clauses and drafting.</p><div className={ui.listItem}><b>Document Checker</b><div className={ui.muted}>Spot areas that may need attention.</div></div><div className={ui.listItem}><b>Clause Checker</b><div className={ui.muted}>Understand important clauses.</div></div><div className={ui.listItem}><b>Document Explainer</b><div className={ui.muted}>Get simpler explanations.</div></div></div><div style={{marginTop:16}}>{lawyers.slice(0,2).map(l=><div key={l.slug} style={{marginBottom:12}}><LawyerCard lawyer={l} compact/></div>)}</div></div></div></section>
   </div>
 </LafreShell>
}
